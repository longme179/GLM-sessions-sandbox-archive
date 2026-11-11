#!/usr/bin/env python3
"""wsclient.py — minimal raw-socket WebSocket console client (memtest harness).

Keeps ONE /console/{id} connection open for the whole measurement window,
exactly like the "SW" scenario of the v1.9.3 report (§12.2):

- plain TCP socket, HTTP/1.1 Upgrade handshake carrying
  `Authorization: Bearer <token>` (daemon auth, 401 -> abort);
- answers server pings with pongs (client->server frames MASKED, RFC 6455);
- counts received text frames (backfill hello + per-line log events) so the
  report can prove the console consumer was really streaming;
- exits cleanly after --duration; prints one WSSTATS line to stderr.

STANDALONE tool (policy Q8): never commit this into the Minewrap app repo.
"""

from __future__ import annotations

import argparse
import base64
import os
import secrets
import signal
import socket
import struct
import sys
import time
from urllib.parse import urlparse

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# set by SIGTERM so the stats line still prints when the runner stops us
_STOP = {"flag": False}


def _on_term(signum, frame):
    _STOP["flag"] = True


def mask_bytes(data: bytes) -> tuple[bytes, bytes]:
    key = secrets.token_bytes(4)
    out = bytes(b ^ key[i % 4] for i, b in enumerate(data))
    return key, out


def build_frame(opcode: int, payload: bytes = b"", mask: bool = True) -> bytes:
    """Serialize one WebSocket frame (client style: masked by default)."""
    header = bytearray()
    header.append(0x80 | opcode)  # FIN + opcode
    length = len(payload)
    if mask:
        mbit = 0x80
    else:
        mbit = 0x00
    if length < 126:
        header.append(mbit | length)
    elif length < (1 << 16):
        header.append(mbit | 126)
        header += struct.pack("!H", length)
    else:
        header.append(mbit | 127)
        header += struct.pack("!Q", length)
    if mask:
        key, masked = mask_bytes(payload)
        return bytes(header) + key + masked
    return bytes(header) + payload


class BufSocket:
    """Small buffered reader for incremental frame parsing."""

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buf = b""

    def read_exact(self, n: int, deadline: float) -> bytes | None:
        while len(self.buf) < n:
            if time.monotonic() > deadline:
                return None
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                continue
            if not chunk:
                raise ConnectionError("socket closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def read_until(self, sep: bytes, deadline: float) -> bytes | None:
        while sep not in self.buf:
            if time.monotonic() > deadline:
                return None
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                continue
            if not chunk:
                raise ConnectionError("socket closed")
            self.buf += chunk
        out, self.buf = self.buf.split(sep, 1)
        return out


def parse_frame(reader: BufSocket, deadline: float):
    """Return (opcode, payload) or None on timeout, raise on close/error."""
    head = reader.read_exact(2, deadline)
    if head is None:
        return None
    opcode = head[0] & 0x0F
    masked = bool(head[1] & 0x80)
    length = head[1] & 0x7F
    if length == 126:
        ext = reader.read_exact(2, deadline)
        if ext is None:
            return None
        length = struct.unpack("!H", ext)[0]
    elif length == 127:
        ext = reader.read_exact(8, deadline)
        if ext is None:
            return None
        length = struct.unpack("!Q", ext)[0]
    if length > (1 << 24):  # 16 MiB sanity cap
        raise ConnectionError(f"oversized frame: {length}")
    mask_key = b""
    if masked:
        mk = reader.read_exact(4, deadline)
        if mk is None:
            return None
        mask_key = mk
    payload = reader.read_exact(length, deadline) if length else b""
    if payload is None:
        return None
    if masked:
        payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
    return opcode, payload


def run(url: str, token: str, duration: float, path_override: str | None) -> int:
    u = urlparse(url)
    host = u.hostname or "127.0.0.1"
    port = u.port or 80
    path = path_override or u.path or "/"

    sock = socket.create_connection((host, port), timeout=5)
    sock.settimeout(1.0)
    reader = BufSocket(sock)

    key = base64.b64encode(secrets.token_bytes(16)).decode()
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        f"Authorization: Bearer {token}\r\n"
        "\r\n"
    )
    sock.sendall(req.encode())

    # read the 101 response head
    deadline = time.monotonic() + 5
    status_line = reader.read_until(b"\r\n", deadline)
    if status_line is None or b" 101 " not in status_line:
        body = status_line or b"<no response>"
        print(f"wsclient: handshake failed: {body!r}", file=sys.stderr)
        return 2
    while True:  # drain remaining headers
        line = reader.read_until(b"\r\n", deadline)
        if line is None or line == b"":
            break

    t0 = time.monotonic()
    messages = 0
    text_bytes = 0
    pings = 0
    log_lines = 0
    while time.monotonic() - t0 < duration and not _STOP["flag"]:
        frame_deadline = min(time.monotonic() + 1.0, t0 + duration)
        try:
            frame = parse_frame(reader, frame_deadline)
        except ConnectionError:
            break
        if frame is None:
            continue
        opcode, payload = frame
        if opcode == 0x9:  # ping -> pong (masked, client style)
            pings += 1
            sock.sendall(build_frame(0xA, payload, mask=True))
        elif opcode == 0x8:  # close -> echo close, done
            try:
                sock.sendall(build_frame(0x8, payload, mask=True))
            except OSError:
                pass
            break
        elif opcode in (0x1, 0x2):  # text / binary
            messages += 1
            text_bytes += len(payload)
            if b'"type":"log"' in payload or b'"type": "log"' in payload:
                log_lines += 1
        # 0x0 continuation and unknown opcodes: ignored (not sent by daemon)

    try:
        sock.sendall(build_frame(0x8, b"", mask=True))
    except OSError:
        pass
    sock.close()
    dt = time.monotonic() - t0
    print(f"WSSTATS duration={dt:.1f}s messages={messages} log_events={log_lines} "
          f"bytes={text_bytes} pings_answered={pings}", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", required=True, help="ws://127.0.0.1:PORT/console/<id>")
    ap.add_argument("--token", required=True)
    ap.add_argument("--duration", type=float, default=35.0)
    ap.add_argument("--path", help="override request path (default: from --url)")
    args = ap.parse_args()
    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGINT, _on_term)
    return run(args.url, args.token, args.duration, args.path)


if __name__ == "__main__":
    sys.exit(main())
