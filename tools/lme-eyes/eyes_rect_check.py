#!/usr/bin/env python3
"""Cross-check the VLM reading against the probe's rect data (nav_trace per click).

nav_trace[i] = {key, point (output), box, reads: [first, settle...]}; the LAST read is
what nav_point believed when it returned the click point. records give ok/react per
page in the same order (variant "all", one nav lookup per page).
"""
import json
from pathlib import Path

RUN = Path("/home/z/my-project/work/vision/s2vision2")
d = json.load(open(RUN / "records.json"))
trace = d["meta"].get("nav_trace") or []

clicks = []
for r in d["records"]:
    if r.get("scenario") != "s2" or r.get("variant") != "all":
        continue
    for p in r.get("pages") or []:
        if p.get("unreachable"):
            continue
        clicks.append((r["rep"], p["page"], p.get("ok"), p.get("react_ms")))

assert len(trace) == len(clicks), (len(trace), len(clicks))

ok_inside = ok_outside = fail_inside = fail_outside = 0
rows = []
for (rep, page, ok, react), tr in zip(clicks, trace):
    assert tr["key"] == page, (tr["key"], page)
    last = tr["reads"][-1]
    x, y, w, h = last["x"], last["y"], last["w"], last["h"]
    px, py = tr["point"]
    wx, wy = px - tr["box"][0], py - tr["box"][1]
    inside = (x - w / 2) <= wx <= (x + w / 2) and (y - h / 2) <= wy <= (y + h / 2)
    if ok:
        ok_inside += inside
        ok_outside += not inside
    else:
        fail_inside += inside
        fail_outside += not inside
    rows.append((rep, page, ok, wx, wy, x, y, w, h, inside))

for rep, page, ok, wx, wy, x, y, w, h, inside in rows:
    if not ok:
        print(f"rep{rep} FAIL {page:<14} click_win=({wx:.0f},{wy:.0f}) rect_c=({x:.0f},{y:.0f}) "
              f"{w:.0f}x{h:.0f} {'IN' if inside else 'OUT'} dy={wy - y:+.0f}px "
              f"dist_to_edge={min(abs(wy - (y - h / 2)), abs((y + h / 2) - wy)):.0f}px")

print(f"\nOK   : inside={ok_inside} outside={ok_outside}")
print(f"FAIL : inside={fail_inside} outside={fail_outside}")
print("\n=> clicks the probe believed were on the delegate, yet navigation never happened:"
      f" {fail_inside}")
