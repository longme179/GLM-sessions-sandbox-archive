#!/usr/bin/env python3
"""scenario.py — run one daemon memtest scenario (Minewrap harness, standalone).

Reproduces the v1.9.3 report §12.2 runner:
  1. wipe the scenario data_dir (fresh token + state every run),
  2. spawn the RELEASE minewrapd binary with MINEWRAP_CONFIG=<scenario.toml>,
     cwd = harness root, stdout/stderr -> results/logs/<label>.log,
  3. wait for GET /health == 200, read the bearer token from <data_dir>/token,
  4. optionally POST /api/v1/instances/<id>/start and wait for "online"
     (fakejava bursts 2000 lines then prints the Done line),
  5. optionally attach ONE raw-socket WS console client (wsclient.py),
  6. sample the daemon process tree with memsample for --seconds (1 Hz),
  7. cleanup: stop instances gracefully, kill the stub subtree, SIGKILL daemon.

Outputs: results/csv_<label>.csv + results/<label>.json (median [min-max]).

STANDALONE tool (policy Q8): never commit this into the Minewrap app repo.
Usage:
  scenario.py --config configs/run.toml --binary ../target/release/minewrapd \\
              --label SR --seconds 35 --start survival
  scenario.py --config configs/run.toml --binary ... --label SW --seconds 35 \\
              --start survival --ws survival
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import memsample  # noqa: E402

MARKER = "fakejava"


def resolve_cfg_path(config_path: str, rel: str) -> str:
    """Daemon semantics (config.rs resolve_paths): relative paths in the
    TOML resolve against the CONFIG FILE's directory, not the cwd."""
    p = os.path.join(os.path.dirname(os.path.abspath(config_path)), rel)
    return os.path.normpath(p)


def ensure_stub_links(config_path: str, cfg: dict) -> None:
    """Symlink the fakejava stub into every work_dir: the daemon spawns
    java_path with cwd=work_dir, so \"./fakejava\" must exist THERE."""
    stub = os.path.join(HERE, "fakejava")
    for inst in cfg.get("instances", []):
        wd = resolve_cfg_path(config_path, inst["work_dir"])
        os.makedirs(wd, exist_ok=True)
        link = os.path.join(wd, "fakejava")
        if not os.path.lexists(link):
            os.symlink(os.path.relpath(stub, wd), link)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def http(method: str, url: str, token: str | None = None, timeout: float = 3.0):
    req = urllib.request.Request(url, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def wait_health(port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            st, _ = http("GET", f"http://127.0.0.1:{port}/health", timeout=1)
            if st == 200:
                return True
        except (urllib.error.URLError, OSError, TimeoutError):
            pass
        time.sleep(0.25)
    return False


def wait_stub_online(port: int, token: str, iid: str, timeout: float = 25.0) -> bool:
    """v1.9.3 daemon: REST combined_state stays 'offline' forever (GapB —
    nothing updates InstanceState). Wait on real signals instead: the Done
    line landed in the LogBuffer AND last_seq keeps growing (0.5 s stream)."""
    deadline = time.time() + timeout
    prev_seq = None
    while time.time() < deadline:
        st, body = http("GET",
                        f"http://127.0.0.1:{port}/api/v1/instances/{iid}/logs?limit=500",
                        token)
        if st == 200:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
            seq = data.get("last_seq") or 0
            done = any("Done (" in (l.get("line") or "")
                       for l in data.get("lines", []))
            if done and prev_seq is not None and seq > prev_seq:
                return True
            prev_seq = seq
        time.sleep(0.4)
    return False


def rest_state(port: int, token: str, iid: str) -> str:
    st, body = http("GET", f"http://127.0.0.1:{port}/api/v1/instances/{iid}", token)
    if st == 200:
        try:
            return json.loads(body).get("combined_state", "?")
        except json.JSONDecodeError:
            return "?"
    return f"http_{st}"


def tree_pids(root: int) -> list[int]:
    """All pids in the process tree under root (inclusive)."""
    procs = memsample.scan_procs()
    included, _ = memsample.collect_tree(procs, root, [])
    return sorted(included)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", required=True, help="scenario TOML (see configs/)")
    ap.add_argument("--binary", required=True, help="minewrapd RELEASE binary")
    ap.add_argument("--label", required=True, help="e.g. S0, SR, SW (suffix #n for runs)")
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--start", help="instance id to start after /health")
    ap.add_argument("--ws", help="instance id whose /console to subscribe (SW)")
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--settle", type=float, default=3.0,
                    help="seconds to wait after start/ws before sampling")
    ap.add_argument("--out-dir", default=os.path.join(HERE, "results"))
    args = ap.parse_args()

    with open(args.config, "rb") as f:
        cfg = tomllib.load(f)
    port = cfg["daemon"]["port"]
    data_dir = resolve_cfg_path(args.config, cfg["daemon"]["data_dir"])
    os.makedirs(args.out_dir, exist_ok=True)
    os.makedirs(os.path.join(args.out_dir, "logs"), exist_ok=True)

    # fresh measurement state
    shutil.rmtree(data_dir, ignore_errors=True)
    os.makedirs(data_dir, exist_ok=True)
    ensure_stub_links(args.config, cfg)

    daemon_log = open(os.path.join(args.out_dir, "logs", f"{args.label}-daemon.log"), "w")
    env = dict(os.environ)
    env["MINEWRAP_CONFIG"] = os.path.abspath(args.config)
    daemon = subprocess.Popen(
        [os.path.abspath(args.binary)],
        cwd=HERE, env=env, stdout=daemon_log, stderr=subprocess.STDOUT,
    )
    print(f"scenario[{args.label}]: daemon pid {daemon.pid}, port {port}")

    ws_proc = None
    try:
        if not wait_health(port):
            print(f"scenario[{args.label}]: /health never came up — FAIL",
                  file=sys.stderr)
            return 1
        token_file = os.path.join(data_dir, "token")
        with open(token_file) as f:
            token = f.read().strip()

        if args.start:
            st, body = http("POST",
                            f"http://127.0.0.1:{port}/api/v1/instances/{args.start}/start",
                            token)
            if st != 200:
                print(f"scenario[{args.label}]: start -> {st} {body}", file=sys.stderr)
                return 1
            if not wait_stub_online(port, token, args.start):
                print(f"scenario[{args.label}]: stub never reached online "
                    "(no Done line / no stream) — check results/logs", file=sys.stderr)
                return 1
            # GapB evidence: the REST snapshot state itself stays stale
            stale = rest_state(port, token, args.start)
            print(f"scenario[{args.label}]: stub online (Done line + stream); "
                  f"REST combined_state={stale!r} (GapB — expected 'offline' "
                  "in v1.9.3 daemon)")

        if args.ws:
            ws_proc = subprocess.Popen(
                [sys.executable, os.path.join(HERE, "wsclient.py"),
                 "--url", f"ws://127.0.0.1:{port}/console/{args.ws}",
                 "--token", token, "--duration", str(args.seconds + 10)],
                stderr=subprocess.PIPE)
        if args.settle > 0:
            time.sleep(args.settle)

        csv_path = os.path.join(args.out_dir, f"csv_{args.label}.csv")
        json_path = os.path.join(args.out_dir, f"{args.label}.json")
        extra = {
            "kind": "daemon",
            "config": os.path.relpath(args.config, HERE),
            "port": port,
            "started_instance": args.start,
            "ws_attached": bool(args.ws),
            "daemon_binary_sha256_16": sha256_file(args.binary),
        }
        if args.start:
            extra["rest_combined_state_after_start"] = rest_state(port, token, args.start)
        summary = memsample.run_sampling(
            daemon.pid, args.seconds, args.interval, csv_path, json_path,
            [MARKER], args.label, extra=extra)
        ok = summary["samples"] >= int(args.seconds / args.interval) - 2

        # capture WS stats (wsclient prints WSSTATS on exit / SIGTERM)
        if ws_proc:
            ws_proc.terminate()
            try:
                _, ws_err = ws_proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                ws_proc.kill()
                _, ws_err = ws_proc.communicate()
            ws_line = (ws_err or b"").decode().strip().splitlines()
            ws_line = [l for l in ws_line if l.startswith("WSSTATS")]
            if ws_line:
                print(f"scenario[{args.label}]: {ws_line[0]}")
                kv = dict(p.split("=", 1) for p in ws_line[0].split()[1:])
                summary["ws"] = kv
                with open(json_path, "w") as fh:
                    json.dump(summary, fh, indent=2)
        return 0 if ok else 1
    finally:
        # cleanup: WS client, instance processes (stub subtree), daemon
        if ws_proc and ws_proc.poll() is None:
            ws_proc.terminate()
            try:
                ws_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                ws_proc.kill()
        for pid in tree_pids(daemon.pid):
            if pid != daemon.pid:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        daemon.kill()
        daemon.wait()
        daemon_log.close()
        # belt & braces (report did `pkill fakejava`): kill any stray stub
        subprocess.run(["pkill", "-f", MARKER], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    sys.exit(main())
