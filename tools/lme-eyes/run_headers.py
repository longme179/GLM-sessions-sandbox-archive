#!/usr/bin/env python3
"""Run headers for the hand-off: harness version, tree, time span, end state of each run.

Usage: python3 -I run_headers.py <run dir> [<run dir> ...]"""
import json
import os
import sys

for run in sys.argv[1:]:
    name = os.path.basename(run.rstrip("/"))
    summary = os.path.join(run, "summary.json")
    md = os.path.join(run, "summary.md")
    meta_p = os.path.join(run, "meta.json")
    print(f"== {name}")
    if os.path.exists(md):
        with open(md) as handle:
            for _ in range(2):
                print("   md:", handle.readline().rstrip()[:260])
    if os.path.exists(summary):
        data = json.load(open(summary))
        print("   summary.run:", json.dumps(data.get("run"))[:700])
    if os.path.exists(meta_p):
        meta = json.load(open(meta_p))
        keep = {k: meta[k] for k in meta if k in ("provenance", "started", "ended", "eyes", "restore_ok",
                                                  "workspace_before", "workspace_after", "workspace_back")}
        keep["restore_ok"] = (meta.get("restore") or {}).get("ok")
        print("   meta:", json.dumps(keep)[:900])
