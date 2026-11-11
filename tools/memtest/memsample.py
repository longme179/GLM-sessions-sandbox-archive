#!/usr/bin/env python3
"""memsample.py — process-tree memory sampler (Minewrap memtest harness).

Reproduces the measurement methodology of the v1.9.3 architecture report
(§12.2), so numbers are directly comparable with that baseline:

- walks the process tree from a root pid via /proc/<pid>/status `PPid`;
- samples at 1 Hz (default): per surviving process reads
  /proc/<pid>/smaps_rollup — RSS, PSS, USS (Private_Clean + Private_Dirty),
  Swap — plus /proc/<pid>/status for Threads / VmPeak / VmHWM;
- EXCLUDES whole subtrees whose root cmdline contains any --exclude-marker
  (the fake-server stub). Children without the marker (`sleep`, subshells)
  are cut too because the parent subtree is dropped — the report's
  hard-won rule (early attempts mis-counted stub children: VmPeak +368 MiB);
- CSV columns: t,rss,pss,uss,swap,threads,procs,vmpeak,hwm
  (MiB for size columns; kB in /proc divided by 1024);
- JSON summary: median [min..max] per column + provenance.

STANDALONE tool (policy Q8): never commit this into the Minewrap app repo.
Usage:
  memsample.py --pid 12345 --seconds 30 --csv out.csv --json out.json \
               [--interval 1.0] [--exclude-marker fakejava] [--label S0]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
import time
from collections import deque

MiB = 1024.0  # /proc reports kB

COLUMNS = ["t", "rss", "pss", "uss", "swap", "threads", "procs", "vmpeak", "hwm"]


def read_file(path: str) -> bytes | None:
    try:
        with open(path, "rb") as f:
            return f.read()
    except (FileNotFoundError, ProcessLookupError, PermissionError, IsADirectoryError):
        return None


def parse_status(data: bytes) -> dict:
    """Extract PPid, Threads, VmPeak, VmHWM (all kB) from /proc/<pid>/status."""
    out = {}
    for line in data.decode("utf-8", "replace").splitlines():
        if line.startswith(("PPid:", "Threads:", "VmPeak:", "VmHWM:")):
            key, _, rest = line.partition(":")
            fields = rest.split()
            if fields:
                try:
                    out[key] = int(fields[0])
                except ValueError:
                    pass
    return out


def parse_smaps_rollup(data: bytes) -> dict:
    """Rss / Pss / Private_Clean / Private_Dirty / Swap in kB -> USS sum."""
    v = {"rss": 0, "pss": 0, "uss": 0, "swap": 0}
    for line in data.decode("utf-8", "replace").splitlines():
        if line.startswith("Rss:"):
            v["rss"] += _kb(line)
        elif line.startswith("Pss:"):
            v["pss"] += _kb(line)
        elif line.startswith("Private_Clean:") or line.startswith("Private_Dirty:"):
            v["uss"] += _kb(line)
        elif line.startswith("Swap:"):
            v["swap"] += _kb(line)
    return v


def _kb(line: str) -> int:
    fields = line.split()
    if len(fields) < 2:
        return 0
    try:
        return int(fields[1])
    except ValueError:
        return 0


def scan_procs() -> dict:
    """Snapshot /proc: pid -> {ppid, threads, vmpeak, vmhwm, cmdline}."""
    procs = {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        raw = read_file(f"/proc/{pid}/status")
        if raw is None:
            continue
        st = parse_status(raw)
        cmd = read_file(f"/proc/{pid}/cmdline")
        cmdline = cmd.decode("utf-8", "replace").replace("\0", " ").strip() if cmd else ""
        procs[pid] = {
            "ppid": st.get("PPid", 0),
            "threads": st.get("Threads", 0),
            "vmpeak": st.get("VmPeak", 0),
            "vmhwm": st.get("VmHWM", 0),
            "cmdline": cmdline,
        }
    return procs


def collect_tree(procs: dict, root: int, markers: list[str]) -> tuple[set, set]:
    """BFS from root. Any non-root node whose cmdline contains a marker is
    excluded TOGETHER WITH its whole subtree (report §12.2 stub rule).
    Returns (included_pids, excluded_pids)."""
    children: dict[int, list] = {}
    for pid, info in procs.items():
        children.setdefault(info["ppid"], []).append(pid)

    included: set = set()
    excluded: set = set()
    q = deque([root])
    while q:
        pid = q.popleft()
        if pid in included or pid in excluded or pid not in procs:
            continue
        info = procs[pid]
        if pid != root and any(m and m in info["cmdline"] for m in markers):
            # cut the entire subtree, not just this pid
            sub = deque([pid])
            while sub:
                x = sub.popleft()
                if x in excluded or x not in procs:
                    continue
                excluded.add(x)
                sub.extend(children.get(x, []))
            continue
        included.add(pid)
        q.extend(children.get(pid, []))
    return included, excluded


def sample_once(procs: dict, included: set) -> dict:
    tot = {"rss": 0, "pss": 0, "uss": 0, "swap": 0, "threads": 0, "vmpeak": 0, "vmhwm": 0}
    for pid in included:
        info = procs.get(pid)
        if info is None:
            continue
        sm = read_file(f"/proc/{pid}/smaps_rollup")
        if sm is None:  # died between scan and read -> skip whole proc
            continue
        v = parse_smaps_rollup(sm)
        tot["rss"] += v["rss"]
        tot["pss"] += v["pss"]
        tot["uss"] += v["uss"]
        tot["swap"] += v["swap"]
        tot["threads"] += info["threads"]
        tot["vmpeak"] += info["vmpeak"]
        tot["vmhwm"] += info["vmhwm"]
    tot["procs"] = len(included)
    return tot


def run_sampling(root: int, seconds: float, interval: float, csv_path: str,
                 json_path: str | None, markers: list[str], label: str = "",
                 extra: dict | None = None) -> dict:
    """Sample the tree under `root` for `seconds`; write CSV + JSON summary.
    Returns the summary dict. Exits early (with note) if the root dies."""
    rows = []
    n_ticks = max(1, int(round(seconds / interval)))
    t0 = time.monotonic()
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        for i in range(n_ticks):
            procs = scan_procs()
            if root not in procs:
                print(f"memsample: root pid {root} disappeared after "
                      f"{time.monotonic()-t0:.1f}s — stopping early", file=sys.stderr)
                break
            included, excluded = collect_tree(procs, root, markers)
            tot = sample_once(procs, included)
            row = [
                round(i * interval, 1),
                round(tot["rss"] / MiB, 3),
                round(tot["pss"] / MiB, 3),
                round(tot["uss"] / MiB, 3),
                round(tot["swap"] / MiB, 3),
                tot["threads"],
                tot["procs"],
                round(tot["vmpeak"] / MiB, 2),
                round(tot["vmhwm"] / MiB, 2),
            ]
            rows.append(row)
            w.writerow(row)
            fh.flush()
            # wall-clock aligned sleep
            target = t0 + (i + 1) * interval
            delay = target - time.monotonic()
            if delay > 0:
                time.sleep(delay)

    summary = {"label": label, "root_pid": root, "seconds": seconds,
               "interval": interval, "markers": markers,
               "samples": len(rows), "columns": COLUMNS,
               "median": {}, "min": {}, "max": {}}
    for idx, col in enumerate(COLUMNS):
        vals = [r[idx] for r in rows] or [0]
        summary["median"][col] = round(statistics.median(vals), 3)
        summary["min"][col] = round(min(vals), 3)
        summary["max"][col] = round(max(vals), 3)
    summary["stable_rss_mib"] = round(summary["max"]["rss"] - summary["min"]["rss"], 3)
    if extra:
        summary.update(extra)
    if json_path:
        with open(json_path, "w") as fh:
            json.dump(summary, fh, indent=2)
    print(f"memsample[{label or root}]: {len(rows)} samples | "
          f"RSS {summary['median']['rss']:.2f} [{summary['min']['rss']:.2f}–"
          f"{summary['max']['rss']:.2f}] MiB | PSS {summary['median']['pss']:.2f} | "
          f"USS {summary['median']['uss']:.2f} | threads {summary['median']['threads']} "
          f"| procs {summary['median']['procs']}")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pid", type=int, required=True, help="root pid of the tree")
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--json")
    ap.add_argument("--label", default="")
    ap.add_argument("--exclude-marker", action="append", default=[],
                    help="cmdline marker whose subtree is excluded (repeatable)")
    args = ap.parse_args()
    run_sampling(args.pid, args.seconds, args.interval, args.csv, args.json,
                 args.exclude_marker, args.label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
