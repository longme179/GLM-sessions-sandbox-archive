#!/usr/bin/env python3
"""Agent-2: minimal raw Wayland client that owns a wlr virtual pointer.

For PRIVATE headless compositors only (the probe's sway): it moves and clicks the pointer
of the private seat, so no real device and no user session is ever touched.

    from vpointer import VirtualPointer
    pointer = VirtualPointer(socket_path)          # raises if the compositor lacks the protocol
    pointer.move(x, y)                              # absolute, 0..1919 x 0..1079
    pointer.click(0x110)                            # BTN_LEFT

Wire protocol only (no libwayland): wl_display.get_registry + sync to list globals, bind the
seat and zwlr_virtual_pointer_manager_v1 at version 1, then motion_absolute / button / frame.
Manager requests: create_virtual_pointer 0, destroy 1, create_virtual_pointer_with_output 2.
"""
import os
import socket
import struct
import time

MANAGER = "zwlr_virtual_pointer_manager_v1"
DISPLAY, REGISTRY, SYNC_CB = 1, 2, 3          # fixed object ids used by this client
# libwayland only accepts the next free client id (wl_map_reserve_new), so every new object
# takes the next number: 4 = seat, 5 = manager, 6 = pointer, then 7, 8, ... for sync callbacks.
SEAT, MANAGER_ID, POINTER, CALLBACK = 4, 5, 6, 7
EXTENT = (1920, 1080)


class VirtualPointer:
    def __init__(self, display: str, runtime: str):
        path = display if display.startswith("/") else os.path.join(runtime, display)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(path)
        self.buf = b""
        self.started = time.monotonic()
        self.globals = []
        self.fresh = CALLBACK                                  # next new object id
        found = self._globals()
        seat = next((g for g in found if g[1] == "wl_seat"), None)
        manager = next((g for g in found if g[1] == MANAGER), None)
        if not seat or not manager:
            raise RuntimeError(f"compositor lacks {MANAGER}; globals: {sorted(g[1] for g in found)}")
        # Requests are processed in order, so no round trip is needed (and a sync here is
        # refused: libwayland only accepts the next free id, see sync()).
        self.bind(seat, 1, SEAT)
        self.bind(manager, 1, MANAGER_ID)
        self._send(MANAGER_ID, 0, struct.pack("<II", SEAT, POINTER))   # create_virtual_pointer (0; 1 is destroy)

    def sync(self) -> None:
        """Round trip for debugging only: raises with the compositor's message on a protocol error."""
        self.fresh += 1
        self._send(DISPLAY, 0, struct.pack("<I", self.fresh))  # wl_display.sync (next free id)
        while True:
            obj, opcode, payload = self._event()
            if obj == DISPLAY and opcode == 0:                 # wl_display.error
                raise RuntimeError(f"wayland protocol error: {payload!r}")
            if obj == self.fresh:                              # wl_callback.done
                return

    # -- wire helpers -------------------------------------------------------------------------------
    def poll(self) -> None:
        """Consume whatever the compositor has sent so far; raises on a protocol error or EOF."""
        self.sock.setblocking(False)
        try:
            while True:
                try:
                    chunk = self.sock.recv(65536)
                except BlockingIOError:
                    return
                if not chunk:
                    raise EOFError("compositor closed the connection")
                self.buf += chunk
                while len(self.buf) >= 8:
                    obj, word = struct.unpack("<II", self.buf[:8])
                    size = word >> 16
                    if len(self.buf) < size:
                        break
                    payload, self.buf = self.buf[8:size], self.buf[size:]
                    if obj == DISPLAY and word & 0xFFFF == 0:
                        raise RuntimeError(f"wayland protocol error: {payload!r}")
        finally:
            self.sock.setblocking(True)

    def _send(self, obj: int, opcode: int, payload: bytes = b"") -> None:
        self.sock.sendall(struct.pack("<II", obj, ((8 + len(payload)) << 16) | opcode) + payload)

    @staticmethod
    def _string(text: str) -> bytes:
        raw = text.encode() + b"\0"
        return struct.pack("<I", len(raw)) + raw + b"\0" * (-len(raw) % 4)

    def _read(self, count: int) -> bytes:
        while len(self.buf) < count:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError("compositor closed the connection")
            self.buf += chunk
        out, self.buf = self.buf[:count], self.buf[count:]
        return out

    def _event(self):
        obj, word = struct.unpack("<II", self._read(8))
        return obj, word & 0xFFFF, self._read((word >> 16) - 8)

    def _globals(self):
        self._send(DISPLAY, 1, struct.pack("<I", REGISTRY))   # wl_display.get_registry
        self._send(DISPLAY, 0, struct.pack("<I", SYNC_CB))    # wl_display.sync
        found = []
        while True:
            obj, opcode, payload = self._event()
            if obj == DISPLAY and opcode == 0:
                raise RuntimeError(f"wayland protocol error: {payload!r}")
            if obj == REGISTRY and opcode == 0:               # wl_registry.global
                name, length = struct.unpack("<II", payload[:8])
                interface = payload[8:8 + length].rstrip(b"\0").decode()
                start = 8 + length + (-length % 4)
                version, = struct.unpack("<I", payload[start:start + 4])
                found.append((name, interface, version))
            if obj == SYNC_CB:                                # wl_callback.done
                return found

    def bind(self, global_, version: int, obj: int) -> None:
        name, interface, available = global_
        self._send(REGISTRY, 0, struct.pack("<I", name) + self._string(interface)
                   + struct.pack("<II", min(version, available), obj))

    # -- actions ------------------------------------------------------------------------------------
    def _time(self) -> int:
        return int((time.monotonic() - self.started) * 1000)

    def frame(self) -> None:
        self._send(POINTER, 4)

    def move(self, x: int, y: int) -> None:
        self._send(POINTER, 1, struct.pack("<IIIII", self._time(), int(x), int(y), *EXTENT))
        self.frame()

    def button(self, code: int, pressed: bool) -> None:
        self._send(POINTER, 2, struct.pack("<III", self._time(), code, 1 if pressed else 0))
        self.frame()

    def click(self, code: int = 0x110) -> None:
        self.button(code, True)
        time.sleep(0.08)
        self.button(code, False)

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass
