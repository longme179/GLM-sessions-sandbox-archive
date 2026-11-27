#!/usr/bin/env python3
"""S1 / S3 side by side: main (A) against the branch (B), number by number.

Usage: python3 -I s1s3_ab_compare.py A:<label> [A:<label> ...] B:<label> [B:<label> ...] [--out FILE]
Each label is a run directory under download/perf-responsive-v2/runs/; a run counts by the
scenarios it holds (S1 ordered+random, S1 fast, S3). Cells are median / p95 (nearest rank) / max
in ms, with N in brackets; clicks without a value are counted apart ("no value").
"""
import json
import math
import os
import sys

RUNS = "/home/z/my-project/download/perf-responsive-v2/runs"
OUT = "/home/z/my-project/download/perf-responsive-v2/eyes-analysis/AB-S1S3-COMPARE.txt"
args = sys.argv[1:]
out = OUT
if "--out" in args:
    out = args[args.index("--out") + 1]
    del args[args.index("--out"):args.index("--out") + 2]

sides = {"A": [], "B": []}
for arg in args:
    side, _, label = arg.partition(":")
    directory = f"{RUNS}/{label}"
    if not os.path.exists(f"{directory}/records.json"):
        print(f"{side} {label}: no records.json under {directory}")
        continue
    data = json.load(open(f"{directory}/records.json"))
    sides[side].append({"label": label, "dir": directory, "data": data,
                        "summary": json.load(open(f"{directory}/summary.json")) if os.path.exists(f"{directory}/summary.json") else {}})

lines = []


def say(text=""):
    lines.append(text)


def stats(values):
    values = sorted(v for v in values if isinstance(v, (int, float)))
    if not values:
        return "– (n=0)"
    mid = len(values) // 2
    median = values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2
    p95 = values[min(len(values) - 1, math.ceil(0.95 * len(values)) - 1)]
    return f"{median:.2f} / {p95:.2f} / {values[-1]:.2f} (n={len(values)})"


def missed(values):
    return sum(1 for v in values if v is None)


def records(side, scenario, variant=None):
    found = []
    for run in sides[side]:
        for rec in run["data"]["records"]:
            if rec.get("scenario") == scenario and (variant is None or rec.get("variant") == variant):
                found.append(rec)
    return found


def stalls(recs):
    values = [s[0] if isinstance(s, list) else s for rec in recs for s in (rec.get("stalls") or [])]
    worst = max(values, default=0.0)
    return (f"{sum(1 for v in values if v > 100)} / {sum(1 for v in values if v > 300)} / {worst:.0f} ms"
            if values else "0 / 0 / –")


def row(cells, widths=None):
    cells = [str(c) for c in cells]
    say("| " + " | ".join(cells) + " |")


say("S1 / S3, main (A) against the branch (B). Cells: median / p95 / max in ms (n); stalls: count >100 ms / count >300 ms / worst.")
say("Runs: " + "; ".join(f"{side} {run['label']}" for side in ("A", "B") for run in sides[side]))
for side in ("A", "B"):
    for run in sides[side]:
        meta = run["data"].get("meta") or {}
        say(f"  {side} {run['label']}: problems {len(run['data'].get('problems') or [])}, ended {meta.get('ended')}, "
            f"eyes {meta.get('eyes')}, still_reads {len(meta.get('still_reads') or [])}")
say()

# ---- S1 ordered -------------------------------------------------------------------------------------
say("## S1 ordered (every tab once, each page waited for)")
header = ["tab", "A click->built", "B click->built", "A click->settled", "B click->settled"]
row(header)
ordered = {side: records(side, "s1", "ordered") for side in ("A", "B")}
tabs = list(dict.fromkeys(c["tab"] for side in ("A", "B") for rec in ordered[side] for c in rec.get("clicks") or []))


def per_tab(side, tab, key):
    return [c.get(key) for rec in ordered[side] for c in rec.get("clicks") or [] if c["tab"] == tab]


for tab in tabs:
    cells = [tab]
    for key in ("page_ms", "settle_ms"):
        for side in ("A", "B"):
            values = per_tab(side, tab, key)
            cells.append(stats(values) + (f" no value {missed(values)}" if missed(values) else ""))
    row(cells)
for side in ("A", "B"):
    ok = sum(1 for rec in ordered[side] if rec.get("ok"))
    close = [rec.get("close_ms") for rec in ordered[side]]
    final = [rec.get("final_settle_ms") for rec in ordered[side]]
    say(f"{side}: reps ok {ok}/{len(ordered[side])}; last tab click->settled {stats(final)}; ESC->gone {stats(close)}; "
        f"recoveries {sum(1 for rec in ordered[side] if rec.get('close_recovery'))}; stalls {stalls(ordered[side])}")
say()

# ---- S1 random --------------------------------------------------------------------------------------
say("## S1 random (12 clicks, 20-300 ms apart plus the time a screenshot takes)")
row(["side", "rep", "ok", "clicks", "click->select", "no value", "click->tab mark", "no value", "stalls >100/>300/worst",
     "last click->settled", "ESC->gone", "ping"])
for side in ("A", "B"):
    for rec in records(side, "s1", "random"):
        gaps = [round(rec["clicks"][i + 1]["t"] - rec["clicks"][i]["t"]) for i in range(len(rec.get("clicks") or []) - 1)]
        row([side, rec["rep"], rec.get("ok"), len(rec.get("clicks") or []), stats(rec.get("select_ms")), missed(rec.get("select_ms") or []),
             stats(rec.get("react_ms")), missed(rec.get("react_ms") or []), stalls([rec]), rec.get("final_settle_ms"),
             rec.get("close_ms"), rec.get("ping_ms")])
        say(f"    gaps ms: {gaps}")
say()

# ---- S1 fast ----------------------------------------------------------------------------------------
say("## S1 fast (as many clicks as fit in 3 s, no screenshots)")
row(["side", "rep", "ok", "clicks", "first->last click ms", "click->select", "no value", "stalls >100/>300/worst",
     "last click->settled", "ESC->gone"])
for side in ("A", "B"):
    for rec in records(side, "s1", "fast"):
        clicks = rec.get("clicks") or []
        row([side, rec["rep"], rec.get("ok"), len(clicks), round(clicks[-1]["t"] - clicks[0]["t"]) if clicks else None,
             stats(rec.get("select_ms")), missed(rec.get("select_ms") or []), stalls([rec]),
             rec.get("final_settle_ms"), rec.get("close_ms")])
say()

# ---- S3 ---------------------------------------------------------------------------------------------
say("## S3 mixed panels (open, dwell, Escape; 17 steps a rep)")
row(["panel", "A steps", "A open", "B steps", "B open", "A ESC->gone", "B ESC->gone", "A worst stall open/close",
     "B worst stall open/close", "A not closed / recovered", "B not closed / recovered"])
s3 = {side: records(side, "s3") for side in ("A", "B")}
panels = list(dict.fromkeys(step["panel"] for side in ("A", "B") for rec in s3[side] for step in rec.get("steps") or []))


def steps_of(side, panel):
    return [step for rec in s3[side] for step in rec.get("steps") or [] if step["panel"] == panel]


for panel in panels:
    cells = [panel]
    for side in ("A", "B"):
        cells += [len(steps_of(side, panel)), stats(s.get("open_ms") for s in steps_of(side, panel))]
    for side in ("A", "B"):
        cells.append(stats(s.get("close_ms") for s in steps_of(side, panel)))
    for side in ("A", "B"):
        mine = steps_of(side, panel)
        worst = max([v[0] if isinstance(v, list) else v for s in mine
                     for v in (s.get("stalls_open") or []) + (s.get("stalls_close") or [])], default=None)
        cells.append(f"{worst:.0f}" if worst is not None else "–")
    for side in ("A", "B"):
        mine = steps_of(side, panel)
        cells.append(f"{sum(1 for s in mine if not s.get('closed'))} / {sum(1 for s in mine if s.get('recovery'))}")
    row(cells)
for side in ("A", "B"):
    mine = [s for rec in s3[side] for s in rec.get("steps") or []]
    recs = s3[side]
    say(f"{side}: steps {len(mine)}, closed {sum(1 for s in mine if s.get('closed'))}, closed by a harness recovery "
        f"{sum(1 for s in mine if s.get('recovery'))}; stalls {stalls(recs)}; workspace step per rep: "
        + "; ".join(json.dumps(rec.get('workspace'))[:110] for rec in recs))
say()

# ---- eyes -------------------------------------------------------------------------------------------
say("## Eyes: the click points of the S1 screenshots against the tab rects the harness read")
for side in ("A", "B"):
    for run in sides[side]:
        manifest_path = f"{run['dir']}/eyes/manifest.json"
        if not os.path.exists(manifest_path):
            continue
        rects = {}
        for entry in (run["data"].get("meta") or {}).get("s1_tab_rects") or []:
            for tab, rect in entry["rects"].items():
                rects.setdefault(tab, []).append(rect)
        shots = json.load(open(manifest_path))
        shots = shots if isinstance(shots, list) else next((v for v in shots.values() if isinstance(v, list)), [])
        inside = outside = 0
        for shot in shots:
            x, y = shot.get("point") or (None, None)
            if any(abs(x - r["x"]) <= r["w"] / 2 and abs(y - r["y"]) <= r["h"] / 2 for rs in rects.values() for r in rs):
                inside += 1
            else:
                outside += 1
        say(f"{side} {run['label']}: {len(shots)} crops, click point inside a tab button {inside}, outside {outside}; "
            f"buttons " + ", ".join(f"{tab} {round(rs[0]['w'])}x{round(rs[0]['h'])} at ({rs[0]['x']:.1f}, {rs[0]['y']:.1f})"
                                    for tab, rs in sorted(rects.items())))

open(out, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
print("written:", out)
