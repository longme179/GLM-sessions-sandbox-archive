#!/usr/bin/env python3
"""Print the key layout of the records of a run directory (one line per record).

Usage: python3 -I rec_keys.py <run dir> [<run dir> ...]"""
import json
import os
import sys

for run in sys.argv[1:]:
    for name in ("records.json", "summary.json"):
        path = os.path.join(run, name)
        if not os.path.exists(path):
            continue
        data = json.load(open(path))
        if name == "summary.json":
            print(f"== {run}: summary.json keys {sorted(data.keys())}")
            continue
        print(f"== {run}: top keys {sorted(data.keys())}; records {len(data.get('records', []))}")
        for rec in data.get("records", [])[:3]:
            shown = {}
            for key, value in rec.items():
                if isinstance(value, list):
                    shown[key] = f"list[{len(value)}]" + (f" first={json.dumps(value[0])[:90]}" if value else "")
                elif isinstance(value, dict):
                    shown[key] = f"dict{sorted(value.keys())[:8]}"
                else:
                    shown[key] = json.dumps(value)[:60]
            print(f"   scenario={rec.get('scenario')} variant={rec.get('variant')} rep={rec.get('rep')}: {json.dumps(shown)[:900]}")
