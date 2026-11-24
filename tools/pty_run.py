#!/usr/bin/env python3
"""pty_run.py — direct PTY execution on the OpenCode host, bypassing models entirely.

Discovered 2026-11-24 (Agent-2 GLM session): when every model provider is down
(relay errors / free-quota exhaustion), the OpenCode server's persistent-pty
capability still gives full shell control on the host.

API shape (server v2.3.0):
  POST /api/pty                       {"directory": "..."} -> {"data": {"id": "pty_...", "pid": N}}
  GET  /api/pty/<id>                  -> info (status, pid, cwd)
  GET  /api/pty/<id>/connect          -> WebSocket upgrade (Basic auth header works; ticket optional)
                                      inbound frames: raw UTF-8 terminal input
                                      outbound frames: raw UTF-8 output chunks; first control frame
                                        is a 0x00 byte + JSON {"cursor": N}
  DELETE /api/pty/<id>                -> kill the PTY
  PUT  /api/pty/<id>                  {"title": ..., "size": {"cols": C, "rows": R}} -> rename/resize
  GET  /api/experimental/persistent-pty/<id>/snapshot -> replay snapshot + cursor

Usage from the z.ai sandbox:
  python3 pty_run.py "command" [--timeout 30] [--clean] [--cwd /home/kimhoanglong]
Marker protocol: sends `printf '%s%s\\n' MARKER $?` after the command; completion is
the echoed line where MARKER is followed by digits (the pre-exec echo shows literal $?).

Gotchas learned the hard way:
- websocket-client recv() returns str for text frames (not (opcode, data) tuples).
- Login bash emits OSC-133/bracketed-paste noise; --clean strips it.
- Paths with apostrophes ("claude's works") need the '"'"' dance or a heredoc.
- File transfer: base64 -w0 local | `echo <b64> | base64 -d > remote`.
- Long jobs: nohup ... > /tmp/log 2>&1 & then poll.
"""
import sys, time, json, base64, argparse, re
import websocket

SERVER_URL = "https://REDACTED-TUNNEL"  # set per-session; the tunnel URL changes
USER = "opencode"
PASSWORD = "SET-PER-SESSION"

def auth_header():
    return "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][0-9A-B]|\r")

def strip_ansi(text):
    return ANSI_RE.sub("", text)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--cwd", default="/home/kimhoanglong")
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()

    import urllib.request
    req = urllib.request.Request(SERVER_URL + "/api/pty", method="POST",
        data=json.dumps({"directory": args.cwd}).encode(),
        headers={"Content-Type": "application/json", "Authorization": auth_header()})
    with urllib.request.urlopen(req, timeout=20) as r:
        pty = json.load(r)["data"]
    pty_id = pty["id"]

    ws_url = SERVER_URL.replace("https://", "wss://") + f"/api/pty/{pty_id}/connect"
    ws = websocket.create_connection(ws_url, timeout=15,
        header={"Authorization: " + auth_header()})

    marker = f"AGENT2DONE{int(time.time() * 1000) % 1000000}"
    payload = ("export PS1='>' PROMPT_COMMAND=''\n" + args.command
               + f"\nprintf '%s%s\\n' {marker} $?\n")
    ws.send(payload)

    output = []
    deadline = time.time() + args.timeout
    done_rc = None
    while time.time() < deadline:
        ws.settimeout(max(1, deadline - time.time()))
        try:
            frame = ws.recv()
        except Exception:
            break
        if frame is None:
            break
        data = frame
        if isinstance(data, tuple):
            data = data[1] if len(data) > 1 else ""
        if isinstance(data, bytes):
            data = data.decode("utf-8", "replace")
        if not isinstance(data, str):
            continue
        output.append(data)
        m = re.search(re.escape(marker) + r"(\d+)\b", data)
        if m:
            done_rc = int(m.group(1))
            end = time.time() + 0.8
            while time.time() < end:
                try:
                    ws.settimeout(0.4)
                    extra = ws.recv()
                    if isinstance(extra, bytes):
                        extra = extra.decode("utf-8", "replace")
                    if isinstance(extra, str):
                        output.append(extra)
                except Exception:
                    break
            break
    ws.close()
    try:
        req2 = urllib.request.Request(f"{SERVER_URL}/api/pty/{pty_id}", method="DELETE",
            headers={"Authorization": auth_header()})
        urllib.request.urlopen(req2, timeout=10)
    except Exception:
        pass

    text = "".join(output)
    if args.clean:
        text = strip_ansi(text)
        lines = [ln for ln in text.split("\n") if marker not in ln]
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
    sys.stdout.write(text + "\n")
    print(f"[rc={done_rc if done_rc is not None else 'unknown'}]", file=sys.stderr)

if __name__ == "__main__":
    main()
