#!/usr/bin/env python3
"""Agent-2: prepare and run the round-2 Settings stutter probe on the host (scratch trees only).

  python3 -I probe_host2.py prepare --root /tmp/lme-probe2 --name stock
  python3 -I probe_host2.py prepare --root /tmp/lme-probe2 --name fixed --overlay /tmp/lme-probe2/fix
  python3 -I probe_host2.py run --root /tmp/lme-probe2 --name stock-use --src src-stock --script use --seconds 34
  python3 -I probe_host2.py run ... --pointer          (headless: also move a virtual pointer over the window)
  python3 -I probe_host2.py run ... --live             (one window on the user's screen for the run)
  python3 -I probe_host2.py status --root /tmp/lme-probe2

Isolation: the sources are copies under --root (never the live clone); every run gets a fresh
HOME copied from the user's config (the real settings file is only read); a private
XDG_RUNTIME_DIR keeps the probe's IPC away from the live shell; the AppId is changed by the
patch. Headless runs never touch the user's session (private sway + a wlr virtual pointer that
belongs to that private seat only). A --live run only borrows the Wayland socket path.
"""
import argparse
import glob
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vpointer import VirtualPointer  # noqa: E402

LIVE_REPO = Path("/home/kimhoanglong/lme-fedora-niri-qs")
REAL_HOME = Path.home()
REAL_RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
IGNORE = shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".github", "node_modules")
TICK_MS = 1000.0 / os.sysconf("SC_CLK_TCK")
PROBLEM = ("ERROR", "WARNING", "is not a", "Expected token", "Unable", "Cannot assign", "binding loop", "TypeError",
           "ReferenceError", "is not defined")
# Pointer wiggle windows for --pointer, in seconds after launch: (start, duration) repeating every 4.9 s
WIGGLE_START, WIGGLE_LENGTH, WIGGLE_PERIOD, WIGGLE_STEP = 3.4, 2.2, 4.9, 0.09

SWAY_CFG = """output HEADLESS-1 resolution 1920x1080 position 0,0
xwayland disable
"""


def niri_socket() -> str | None:
    found = sorted(glob.glob(str(REAL_RUNTIME / "niri.wayland-*.sock")))
    return found[0] if found else None


def guard_root(root: Path) -> Path:
    root = root.resolve()
    if not str(root).startswith("/tmp/") or root == Path("/tmp"):
        sys.exit(f"REFUSED: --root must be a dedicated directory under /tmp, got {root}")
    return root


def tree_bytes(path: Path) -> tuple[int, int]:
    files = size = 0
    for item in path.rglob("*"):
        if item.is_file() and not item.is_symlink():
            files += 1
            size += item.stat().st_size
    return files, size


def build_home(root: Path) -> None:
    home = root / "home.template"
    if home.exists():
        shutil.rmtree(home)
    config = home / ".config"
    config.mkdir(parents=True)
    shutil.copytree(REAL_HOME / ".config/lme-shell", config / "lme-shell", ignore=shutil.ignore_patterns("*.lock"))
    shutil.copytree(REAL_HOME / ".config/niri", config / "niri")
    for name in (".cache", ".local/state", ".local/share"):
        (home / name).mkdir(parents=True)
    fonts = REAL_HOME / ".local/share/fonts"
    if fonts.is_dir():
        (home / ".local/share/fonts").symlink_to(fonts, target_is_directory=True)
    (root / "sway.cfg").write_text(SWAY_CFG)


def cmd_prepare(root: Path, args) -> int:
    src = root / f"src-{args.name}"
    if src.exists():
        shutil.rmtree(src)
    started = time.monotonic()
    shutil.copytree(LIVE_REPO, src, symlinks=True, ignore=IGNORE)
    files, size = tree_bytes(src)
    print(f"copied {files} files, {size / 1e6:.1f} MB in {time.monotonic() - started:.1f}s")
    overlaid = []
    if args.overlay:
        overlay = Path(args.overlay).resolve()
        for item in sorted(overlay.rglob("*.qml")):
            target = src / item.relative_to(overlay)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(item, target)
            overlaid.append(str(item.relative_to(overlay)))
        print(f"overlay: {len(overlaid)} files: {', '.join(overlaid)}")
    expect = "fixed" if args.overlay else "stock"
    patch = Path(__file__).with_name("probe_patch2.py")
    if subprocess.run([sys.executable, "-I", str(patch), "--src", str(src), "--expect", expect]).returncode:
        return 1
    if args.rebuild_home or not (root / "home.template").exists():
        build_home(root)
    (root / "runs").mkdir(exist_ok=True)

    # The host's /usr/bin/qmllint is the Qt 5 one and stops at `pragma ComponentBehavior`, on the
    # pristine files as well, so the real loader is the only syntax check that counts here.
    smoke = argparse.Namespace(name=f"smoke-{args.name}", src=f"src-{args.name}", live=False, prewarm=1, poll=1,
                               motion=None, seconds=4.0, script="use", pointer=False)
    if cmd_run(root, smoke):
        print("SMOKE RUN FAILED")
        return 1
    log_text = (root / f"runs/smoke-{args.name}/probe.log").read_text(errors="replace")
    problems = sorted({line for line in log_text.splitlines() if any(word in line for word in PROBLEM)})
    for line in problems[:15]:
        print("  " + line[:220])
    print(f"smoke run: {len(problems)} distinct problem lines; {log_text.count(chr(10))} log lines")
    prefs = json.loads((root / "home.template/.config/lme-shell/settings.json").read_text())
    shown = {key: prefs.get(key) for key in ("surfaceStyle", "motionPreset", "motionSpeed", "animations", "density", "reducedTransparency", "fontSize")}
    print("scratch preferences:", json.dumps(shown))
    return 0


def base_env(work: Path, runtime: Path) -> dict:
    home = work / "home"
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "XDG_STATE_HOME": str(home / ".local/state"),
        "XDG_RUNTIME_DIR": str(runtime),
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={REAL_RUNTIME}/bus",
        "LANG": os.environ.get("LANG") or "C.UTF-8",
        "TERM": "dumb",
        "QSG_RENDER_TIMING": "1",
        "QSG_INFO": "1",
        "LME_PROBE_CMDLOG": str(work / "cmd.log"),
    }
    socket = niri_socket()
    if socket:
        env["NIRI_SOCKET"] = socket
    return env


def read_thread_stat(path: Path):
    try:
        data = path.read_text()
    except OSError:
        return None
    close = data.rfind(")")
    fields = data[close + 2:].split()
    return data[data.find("(") + 1:close], int(fields[11]) + int(fields[12])


def sample_cpu(pid: int) -> dict:
    """CPU ticks per thread name for the probe process and its descendants (own processes only)."""
    stack, seen, threads = [pid], set(), {}
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        tasks = Path(f"/proc/{current}/task")
        try:
            tids = os.listdir(tasks)
        except OSError:
            continue
        for tid in tids:
            stat = read_thread_stat(tasks / tid / "stat")
            if stat:
                threads[stat[0]] = threads.get(stat[0], 0) + stat[1]
        try:
            stack.extend(int(kid) for kid in (tasks / str(current) / "children").read_text().split())
        except OSError:
            pass
    return threads


def stop_group(process: subprocess.Popen, grace: float = 4.0) -> None:
    if process is None or process.poll() is not None:
        return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=grace)
            return
        except subprocess.TimeoutExpired:
            continue


def wait_for_socket(runtime: Path, process: subprocess.Popen, limit: float = 15.0) -> str | None:
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        found = sorted(p for p in runtime.glob("wayland-*") if p.suffix != ".lock")
        if found:
            return found[0].name
        if process.poll() is not None:
            return None
        time.sleep(0.1)
    return None


def wiggle(socket: str, runtime: Path, launch: float, until: float, log, errors: list) -> None:
    """Move a virtual pointer over the window during the idle phases of the `mixed` script."""
    try:
        pointer = VirtualPointer(socket, str(runtime))
        moves, step = 0, 0
        while time.monotonic() < until:
            elapsed = time.monotonic() - launch
            phase = (elapsed - WIGGLE_START) % WIGGLE_PERIOD
            if elapsed >= WIGGLE_START and phase < WIGGLE_LENGTH:
                x = 960 + (120 if step % 2 else -120) + (step % 7) * 5
                y = 540 + (90 if step % 3 == 0 else -60) + (step % 5) * 6
                pointer.move(x, y)
                moves += 1
                log.write(f"{time.monotonic():.3f} move {x} {y}\n")
            time.sleep(WIGGLE_STEP)
            step += 1
        pointer.close()
        log.write(f"{time.monotonic():.3f} done moves={moves}\n")
    except Exception as error:  # noqa: BLE001 - reported in the run summary
        errors.append(repr(error))


def cmd_run(root: Path, args) -> int:
    src, work = root / args.src, root / "runs" / args.name
    if not (src / "settings.qml").exists():
        sys.exit(f"no instrumented tree at {src}")
    if work.exists():
        shutil.rmtree(work)
    (work / "home").parent.mkdir(parents=True)
    shutil.copytree(root / "home.template", work / "home", symlinks=True)
    runtime = work / "runtime"
    runtime.mkdir(mode=0o700)
    prefs_path = work / "home/.config/lme-shell/settings.json"
    prefs = json.loads(prefs_path.read_text())
    if args.motion is not None:
        prefs["motionSpeed"] = args.motion
        prefs_path.write_text(json.dumps(prefs, ensure_ascii=False, indent=2))
    env = base_env(work, runtime)
    env.update({
        "LME_PROBE_NOPREWARM": "0" if args.prewarm else "1",
        "LME_PROBE_NOPOLL": "0" if args.poll else "1",
        "LME_PROBE_RUNTIME_MS": str(int(args.seconds * 1000)),
        "LME_PROBE_SCRIPT": args.script,
    })
    meta = {"name": args.name, "src": args.src, "live": args.live, "script": args.script, "pointer": args.pointer,
            "prewarm": args.prewarm, "poll": args.poll, "motionSpeed": prefs.get("motionSpeed"),
            "surfaceStyle": prefs.get("surfaceStyle"), "motionPreset": prefs.get("motionPreset"),
            "loadavg_before": os.getloadavg()}
    sway = probe = None
    pointer_log, pointer_errors, pointer_thread = open(work / "pointer.log", "w"), [], None
    try:
        if args.live:
            env["WAYLAND_DISPLAY"] = str(REAL_RUNTIME / "wayland-1")
        else:
            env.update({"WLR_BACKENDS": "headless", "WLR_LIBINPUT_NO_DEVICES": "1", "WLR_RENDERER": "pixman", "WLR_HEADLESS_OUTPUTS": "1"})
            sway_log = open(work / "sway.log", "w")
            sway = subprocess.Popen(["sway", "-c", str(root / "sway.cfg")], env=env, cwd=work,
                                    stdout=sway_log, stderr=subprocess.STDOUT, start_new_session=True)
            socket = wait_for_socket(runtime, sway)
            if not socket:
                sway_log.close()
                stop_group(sway)
                print(f"headless sway gave no socket; see {work}/sway.log")
                return 1
            env["WAYLAND_DISPLAY"] = socket
            del env["WLR_BACKENDS"], env["WLR_LIBINPUT_NO_DEVICES"], env["WLR_RENDERER"], env["WLR_HEADLESS_OUTPUTS"]
            env.update({"QT_QPA_PLATFORM": "wayland", "QSG_RHI_BACKEND": "opengl", "LIBGL_ALWAYS_SOFTWARE": "1"})
            time.sleep(0.8)
            outputs = ""
            for ipc in runtime.glob("sway-ipc*.sock"):
                reply = subprocess.run(["swaymsg", "-s", str(ipc), "-t", "get_outputs", "-r"], env=env, capture_output=True, text=True)
                outputs = reply.stdout[:2000]
            meta["sway_outputs"] = outputs
            sway_log.close()
            if not args.live:
                # The seat needs a pointer device before the app starts, or Qt never creates one.
                seat_pointer = VirtualPointer(socket, str(runtime))
                seat_pointer.move(1200, 700)
                seat_pointer.close()
                meta["virtual_pointer"] = True

        log = open(work / "probe.log", "w")
        (work / "cmd.log").write_text("")
        launch_wall, launch_mono = time.time(), time.monotonic()
        meta["launch_wall"] = launch_wall
        meta["launch_mono"] = launch_mono
        probe = subprocess.Popen(["quickshell", "-p", str(src / "settings.qml")], env=env, cwd=src,
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        if args.pointer and not args.live:
            socket = env["WAYLAND_DISPLAY"]
            pointer_thread = threading.Thread(
                target=wiggle, args=(socket, runtime, launch_mono, launch_mono + args.seconds, pointer_log, pointer_errors), daemon=True)
            pointer_thread.start()
        samples, deadline = [], launch_mono + args.seconds + 30
        while probe.poll() is None and time.monotonic() < deadline:
            threads = sample_cpu(probe.pid)
            samples.append([round(time.monotonic() - launch_mono, 3), threads])
            time.sleep(0.2)
        timed_out = probe.poll() is None
        stop_group(probe)
        log.close()
        meta.update({"exit": probe.returncode, "timed_out": timed_out, "seconds": round(time.monotonic() - launch_mono, 2),
                     "loadavg_after": os.getloadavg()})
        if pointer_thread is not None:
            pointer_thread.join(timeout=5)
        meta["pointer_errors"] = pointer_errors
    finally:
        stop_group(probe)
        stop_group(sway, 2.0)
        pointer_log.close()
        (work / "samples.json").write_text(json.dumps(samples))
        (work / "meta.json").write_text(json.dumps(meta, indent=1))
    log_text = (work / "probe.log").read_text(errors="replace")
    lines = log_text.count("@@PROBE ")
    print(json.dumps({key: meta.get(key) for key in ("name", "src", "live", "script", "pointer", "exit", "timed_out", "seconds", "motionSpeed")}))
    print(f"probe.log: {len(log_text)} bytes, {lines} probe lines, {log_text.count(chr(10))} lines")
    problems = sorted({line for line in log_text.splitlines() if any(word in line for word in PROBLEM)})
    print(f"{len(problems)} distinct problem lines")
    for line in problems[:12]:
        print("  " + line[:220])
    if pointer_errors:
        print("pointer errors:", pointer_errors)
    if lines == 0:
        print(log_text[-1500:])
    return 0 if lines and not timed_out else 1


def cmd_status(root: Path) -> int:
    for src in sorted(root.glob("src-*")):
        files, size = tree_bytes(src)
        print(f"{src.name}: {files} files, {size / 1e6:.1f} MB")
    for run in sorted((root / "runs").glob("*")):
        log = run / "probe.log"
        print(f"run {run.name}: {log.stat().st_size if log.exists() else 0} bytes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)  # --root is accepted before or after the subcommand
    common.add_argument("--root", default="/tmp/lme-probe2")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", parents=[common])
    prep.add_argument("--name", required=True, choices=("stock", "fixed"))
    prep.add_argument("--overlay", help="directory with the fixed qml files, copied over the live copy")
    prep.add_argument("--rebuild-home", action="store_true")
    run = sub.add_parser("run", parents=[common])
    run.add_argument("--name", required=True)
    run.add_argument("--src", required=True, help="src-stock or src-fixed under --root")
    run.add_argument("--script", default="use", choices=("use", "idle", "mixed", "cold"))
    run.add_argument("--prewarm", type=int, default=1)
    run.add_argument("--poll", type=int, default=1)
    run.add_argument("--motion", type=float, default=None)
    run.add_argument("--seconds", type=float, default=34.0)
    run.add_argument("--live", action="store_true")
    run.add_argument("--pointer", action="store_true", help="headless only: move a virtual pointer over the window")
    sub.add_parser("status", parents=[common])
    args = parser.parse_args()
    root = guard_root(Path(args.root))
    if args.command == "run":
        return cmd_run(root, args)
    if args.command == "prepare":
        return cmd_prepare(root, args)
    return cmd_status(root)


if __name__ == "__main__":
    sys.exit(main())
