#!/usr/bin/env python3
"""gui_scenario.py — measure the minewrap-tauri GUI process tree (memtest).

The "GUI" scenario of the v1.9.3 report (§13.2): launch the GUI with an
isolated MINEWRAP_CONFIG (1 offline instance, private data_dir), wait for
the WebKit process tree to appear and settle, then sample the WHOLE tree
(minewrap-tauri + WebKitWebProcess + WebKitNetworkProcess) for --seconds.

Display: inherits the current session env by default (Wayland/X11). For
headless measurement use --xvfb :99 (sets DISPLAY) — that is also the C4
spike protocol display. Optionally --setenv K=V (repeatable).

STANDALONE tool (policy Q8): never commit this into the Minewrap app repo.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import memsample  # noqa: E402
import scenario  # noqa: E402  (reuse resolve_cfg_path semantics)


def resolve_cfg_path(config_path: str, rel: str) -> str:
    return scenario.resolve_cfg_path(config_path, rel)


def tree_procs(root: int) -> dict:
    procs = memsample.scan_procs()
    return procs


def gui_tree_ready(root: int) -> tuple[bool, int]:
    """True when WebKitWebProcess (or >=2 children) is present in the tree."""
    procs = memsample.scan_procs()
    if root not in procs:
        return False, 0
    included, _ = memsample.collect_tree(procs, root, [])
    n = 0
    for pid in included:
        if "WebKit" in procs[pid]["cmdline"] or "webkit" in procs[pid]["cmdline"]:
            n += 1
    return len(included) >= 2, len(included)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--binary", required=True, help="minewrap-tauri binary")
    ap.add_argument("--config", default=os.path.join(HERE, "configs", "gui.toml"))
    ap.add_argument("--label", default="GUI")
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--settle", type=float, default=8.0,
                    help="seconds after tree appears before sampling starts")
    ap.add_argument("--xvfb", help="e.g. :99 — sets DISPLAY for headless runs")
    ap.add_argument("--setenv", action="append", default=[], metavar="K=V")
    ap.add_argument("--out-dir", default=os.path.join(HERE, "results"))
    args = ap.parse_args()

    with open(args.config, "rb") as f:
        cfg = tomllib.load(f)
    data_dir = resolve_cfg_path(args.config, cfg["daemon"]["data_dir"])
    shutil.rmtree(data_dir, ignore_errors=True)
    os.makedirs(data_dir, exist_ok=True)
    scenario.ensure_stub_links(args.config, cfg)
    os.makedirs(os.path.join(args.out_dir, "logs"), exist_ok=True)

    env = dict(os.environ)
    env["MINEWRAP_CONFIG"] = os.path.abspath(args.config)
    if args.xvfb:
        env["DISPLAY"] = args.xvfb
    for kv in args.setenv:
        k, _, v = kv.partition("=")
        env[k] = v

    log = open(os.path.join(args.out_dir, "logs", f"{args.label}-gui.log"), "w")
    gui = subprocess.Popen([os.path.abspath(args.binary)], cwd=HERE, env=env,
                           stdout=log, stderr=subprocess.STDOUT)
    print(f"gui_scenario[{args.label}]: pid {gui.pid}")

    try:
        # wait for the webview tree (up to 30 s)
        deadline = time.time() + 30
        ready, n = gui_tree_ready(gui.pid)
        while not ready and time.time() < deadline and gui.poll() is None:
            time.sleep(0.5)
            ready, n = gui_tree_ready(gui.pid)
        if gui.poll() is not None:
            print(f"gui_scenario[{args.label}]: GUI exited early "
                  f"(code {gui.returncode}) — see results/logs", file=sys.stderr)
            return 1
        print(f"gui_scenario[{args.label}]: tree procs={n}, settling {args.settle}s")
        time.sleep(args.settle)

        csv_path = os.path.join(args.out_dir, f"csv_{args.label}.csv")
        json_path = os.path.join(args.out_dir, f"{args.label}.json")
        summary = memsample.run_sampling(
            gui.pid, args.seconds, 1.0, csv_path, json_path,
            ["fakejava"], args.label,
            extra={"kind": "gui", "config": os.path.relpath(args.config, HERE),
                   "display": env.get("DISPLAY", ""),
                   "wayland_display": env.get("WAYLAND_DISPLAY", "")},
        )
        ok = summary["samples"] >= int(args.seconds) - 2
        return 0 if ok else 1
    finally:
        gui.terminate()
        try:
            gui.wait(timeout=8)
        except subprocess.TimeoutExpired:
            gui.kill()
            gui.wait()
        log.close()


if __name__ == "__main__":
    sys.exit(main())
