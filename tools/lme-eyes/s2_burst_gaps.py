#!/usr/bin/env python3
"""S2 records: which variants a run holds, and how far apart the clicks really were.

Usage: python3 -I s2_burst_gaps.py <run dir> [<run dir> ...]
Per S2 record: variant, number of clicks, and the gaps between consecutive clicks in ms
(min / median / max). The `aba` and `toast` variants keep their clicks as [[page, at], ...] with
`at` in epoch ms; the `all` variant keeps one entry per page under `pages` with `t` in epoch ms.
`aba` is designed for a 60 ms gap between two clicks."""
import json
import os
import statistics
import sys


def gaps_of(rec):
    clicks = rec.get("clicks") or []
    if clicks and isinstance(clicks[0], (list, tuple)) and len(clicks[0]) >= 2:
        times = [c[1] for c in clicks if isinstance(c[1], (int, float))]
        return [round(b - a) for a, b in zip(times, times[1:])]
    pages = rec.get("pages") or []
    times = [p["t"] for p in pages if isinstance(p, dict) and isinstance(p.get("t"), (int, float))]
    return [round(b - a) for a, b in zip(times, times[1:])]


for run in sys.argv[1:]:
    path = os.path.join(run, "records.json")
    if not os.path.exists(path):
        print(f"{run}: no records.json")
        continue
    data = json.load(open(path))
    recs = [r for r in data.get("records", []) if r.get("scenario") == "s2"]
    name = os.path.basename(run.rstrip("/"))
    print(f"== {name}: {len(recs)} S2 records; problems {len(data.get('problems') or [])}")
    for rec in recs:
        g = gaps_of(rec)
        clicks = rec.get("clicks") or rec.get("pages") or []
        text = f"min {min(g)} / median {statistics.median(g):.0f} / max {max(g)}" if g else "no gaps"
        print(f"   variant {rec.get('variant')} rep {rec.get('rep')} ok {rec.get('ok')} clicks {len(clicks)} "
              f"gap_ms={rec.get('gap_ms')} gaps ms: {text}")
        if len(sys.argv) <= 2:
            print("      ", g[:40])
