#!/usr/bin/env python3
"""Marks and panel-state changes of the shell probe log in a window of epoch ms.

Usage: probe_trace.py <run dir> <t0 epoch ms> <t1 epoch ms> [--every-sample]
The log's clock is ms since the stand-in's epoch (the `sink` line); this converts to epoch.
"""
import json
import sys

run, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
every = "--every-sample" in sys.argv
epoch = None
rows = []
for line in open(f"{run}/probe/probe.shell.log", errors="replace"):
    if not line.startswith("@@PROBE "):
        continue
    parts = line.split()
    if parts[1] == "sink":
        for item in parts[2:]:
            if item.startswith("epoch="):
                epoch = int(item.split("=")[1])
        continue
    if epoch is None or len(parts) < 3:
        continue
    try:
        at = epoch + float(parts[2])
    except ValueError:
        continue
    if not t0 <= at <= t1:
        continue
    if parts[1] == "S":
        try:
            data = json.loads(line[line.index("{"):])
        except ValueError:
            continue
        cc = data.get("cc") or {}
        rows.append((at, "S", data.get("panel"), data.get("panelOpen"), data.get("controlOpen"),
                     (data.get("hosts") or {}).get("cc", {}).get("shown"), cc.get("tab")))
    elif parts[1] in ("m", "F", "k"):
        rows.append((at, parts[1], " ".join(parts[3:])[:90]))

prev = None
for row in sorted(rows):
    at, kind = row[0] - t0, row[1]
    if kind == "S":
        if row[2:] != prev or every:
            print(f"{at:7.0f} S panel={row[2]} panelOpen={row[3]} controlOpen={row[4]} cc.shown={row[5]} cc.tab={row[6]}")
            prev = row[2:]
    else:
        print(f"{at:7.0f} {kind} {row[2]}")
