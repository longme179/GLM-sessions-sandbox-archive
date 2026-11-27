#!/usr/bin/env python3
"""meta.still_reads of a run: how many rect reads each S1 click needed and how far the panel stage
had moved at the last read (the harness reads the tab rects only once the stage is at rest).

Usage: python3 -I still_reads_check.py <run dir> [<run dir> ...]"""
import json
import os
import sys

for run in sys.argv[1:]:
    path = os.path.join(run, "records.json")
    if not os.path.exists(path):
        print(f"{run}: no records.json")
        continue
    meta = json.load(open(path)).get("meta") or {}
    reads = meta.get("still_reads") or []
    name = os.path.basename(run.rstrip("/"))
    if not reads:
        print(f"== {name}: still_reads {len(reads)}")
        continue
    print(f"== {name}: still_reads {len(reads)}; keys {sorted(reads[0].keys())}")
    print("   first:", json.dumps(reads[0])[:300])
    for key in ("reads", "count", "n"):
        if key in reads[0]:
            values = [r.get(key) for r in reads]
            print(f"   {key}: distinct {sorted(set(values))}, max {max(values)}")
    for key in ("moved", "moved_px", "move"):
        if key in reads[0]:
            values = [r.get(key) or 0 for r in reads]
            print(f"   {key}: max {max(values)}")
