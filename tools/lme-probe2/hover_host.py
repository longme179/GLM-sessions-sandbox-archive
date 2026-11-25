#!/usr/bin/env python3
"""Agent-2: run hover_test.qml in a private headless sway and drive a virtual pointer through it.

  python3 -I hover_host.py --src /tmp/lme-probe/src --out /tmp/lme-probe2/hover

Copies hover_test.qml (next to this script) into --src, starts sway headless with a private
XDG_RUNTIME_DIR, moves and clicks a wlr virtual pointer (vpointer.py, private seat only), and
prints the "@@HOVER" lines. Never touches the user's session.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vpointer import VirtualPointer  # noqa: E402

REAL_RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
SWAY_CFG = "output HEADLESS-1 resolution 1920x1080 position 0,0\nxwayland disable\n"

# (label, local x, local y, click?) in window coordinates of hover_test.qml
STEPS = [
    ("blank", 480, 160, False),
    ("blank+40", 520, 200, False),
    ("btn", 140, 40, False),
    ("btn+30", 170, 40, True),
    ("field", 140, 100, False),
    ("field+30", 170, 100, False),
    ("slider", 140, 158, False),
    ("slider+60", 200, 158, False),
    ("plain", 140, 212, False),
    ("plain+30", 170, 212, True),
    ("area", 140, 268, False),
    ("area+30", 170, 268, False),
    ("outside", 1500, 900, False),
    ("blank-again", 480, 160, False),
]


def stop(process, grace=3.0):
    if process is None or process.poll() is not None:
        return
    for sig in (15, 9):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=grace)
            return
        except subprocess.TimeoutExpired:
            continue


def windows(node):
    if isinstance(node, dict):
        if node.get("app_id"):
            yield node
        for value in node.values():
            yield from windows(value)
    elif isinstance(node, list):
        for value in node:
            yield from windows(value)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--src-file", default=str(Path(__file__).with_name("hover_test.qml")))
    args = ap.parse_args()
    src, work = Path(args.src).resolve(), Path(args.out).resolve()
    if (src / ".git").exists() or not str(work).startswith("/tmp/"):
        sys.exit("REFUSED: --src must be a scratch tree and --out a directory under /tmp")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    runtime = work / "runtime"
    runtime.mkdir(mode=0o700)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(work), "XDG_RUNTIME_DIR": str(runtime),
           "DBUS_SESSION_BUS_ADDRESS": f"unix:path={REAL_RUNTIME}/bus", "LANG": os.environ.get("LANG") or "C.UTF-8",
           "TERM": "dumb", "WLR_BACKENDS": "headless", "WLR_LIBINPUT_NO_DEVICES": "1", "WLR_RENDERER": "pixman",
           "WLR_HEADLESS_OUTPUTS": "1", "QT_QPA_PLATFORM": "wayland", "QSG_RHI_BACKEND": "opengl",
           "LIBGL_ALWAYS_SOFTWARE": "1"}
    shutil.copy(args.src_file, src / "hover_test.qml")
    (work / "sway.cfg").write_text(SWAY_CFG)
    sway = app = None
    try:
        sway_log = open(work / "sway.log", "w")
        sway = subprocess.Popen(["sway", "-c", str(work / "sway.cfg")], env=env, cwd=work,
                                stdout=sway_log, stderr=subprocess.STDOUT, start_new_session=True)
        socket = None
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and socket is None:
            found = sorted(p for p in runtime.glob("wayland-*") if p.suffix != ".lock")
            socket = found[0].name if found else None
            time.sleep(0.1)
        if not socket:
            print("sway gave no socket:", (work / "sway.log").read_text()[-800:])
            return 1
        env["WAYLAND_DISPLAY"] = socket
        time.sleep(0.8)
        ipc = sorted(runtime.glob("sway-ipc*.sock"))[0]

        def swaymsg(*command):
            return subprocess.run(["swaymsg", "-s", str(ipc), *command], env=env, capture_output=True, text=True)

        log = open(work / "app.log", "w")
        app = subprocess.Popen(["quickshell", "-p", str(src / "hover_test.qml")], env=env, cwd=src,
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(2.5)
        placed = swaymsg('[app_id="lme-hovertest"]', "floating", "enable", ",", "resize", "set", "600", "320",
                         ",", "move", "position", "100", "100")
        print("place:", placed.returncode, (placed.stderr or placed.stdout).strip()[:200])
        time.sleep(0.8)
        tree = json.loads(swaymsg("-t", "get_tree", "-r").stdout)
        found = [w for w in windows(tree) if "hover" in str(w.get("app_id"))]
        print("windows:", json.dumps([{"app_id": w.get("app_id"), "rect": w.get("rect")} for w in found])[:400])
        if not found:
            print("no window found; app log:", (work / "app.log").read_text()[-1500:])
            return 1
        rect = found[0]["rect"]
        pointer = VirtualPointer(socket, str(runtime))
        time.sleep(0.3)
        pointer.poll()
        print("virtual pointer created")
        for label, x, y, click in STEPS:
            pointer.move(rect["x"] + x, rect["y"] + y)
            time.sleep(0.45)
            pointer.poll()
            print("moved", label)
            if click:
                pointer.click()
                time.sleep(0.3)
        time.sleep(0.4)
    except Exception as error:
        stop(app)
        stop(sway)
        tail = [line for line in (work / "sway.log").read_text(errors="replace").splitlines()[-40:]
                if "rror" in line or "invalid" in line or "unknown" in line]
        print(f"FAILED: {error!r}")
        print("\n".join("  sway: " + line[:220] for line in tail[-8:]))
        return 1
    finally:
        stop(app)
        stop(sway)
    text = (work / "app.log").read_text(errors="replace")
    lines = [line[line.index("@@HOVER"):] for line in text.splitlines() if "@@HOVER" in line]
    print("\n".join(lines))
    other = sorted({line[:160] for line in text.splitlines()
                    if "ERROR" in line or "is not a" in line or "Expected token" in line})
    print(f"{len(lines)} hover lines; {len(other)} distinct error lines")
    for line in other[:10]:
        print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
