#!/usr/bin/env python3
"""Pixel-objective check: was a nav-row button under the crosshair at click time?

For every eyes/*.jpg (440x440 crop, crosshair at the centre): build a horizontal
brightness profile (mean per row, ignoring red crosshair pixels), take its gradient,
find row boundaries (local maxima) above and below the centre. A delegate present
under the crosshair shows as two boundaries roughly 40-60 px apart straddling y=220
(the button row), with icon/label contrast INSIDE. Report distance of the nearest
boundaries for OK vs FAIL clicks.

This replaces VLM guessing with geometry: the probe said the delegate was there; the
pixels say whether a row-shaped object was actually rendered there.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

EYES = Path("/home/z/my-project/work/vision/s2vision2/eyes")
RUN = Path("/home/z/my-project/work/vision/s2vision2")

d = json.load(open(RUN / "records.json"))
trace = d["meta"]["nav_trace"] or []
clicks = []
for r in d["records"]:
    if r.get("scenario") != "s2" or r.get("variant") != "all":
        continue
    for p in r.get("pages") or []:
        if p.get("unreachable"):
            continue
        clicks.append((r["rep"], p["page"], p.get("ok"), p.get("react_ms")))
assert len(trace) == len(clicks)

# Rebuild the true shot order: shots are click_at calls in order; a retry repeats the
# same point. Walk clicks and shots together, consuming a shot when its point matches
# the click's trace point (retry shots appear right after their original).
def near(a, b, tol=2):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol

man = [r for r in json.load(open(EYES / "manifest.json")) if r.get("file", "").endswith(".jpg")]
si = 0
resolved = []          # (rep, page, ok, shot_file)
for rep, page, ok, react in clicks:
    tr = trace[len(resolved)]
    want = (tr["point"][0], tr["point"][1])
    prev = (trace[len(resolved) - 1]["point"][0], trace[len(resolved) - 1]["point"][1]) \
        if resolved else None
    # Consume shots until one sits at this click's point (2 px tolerance: the injector
    # rounds to whole pixels); a shot at the PREVIOUS click's point is its retry.
    while si < len(man):
        p = tuple(man[si]["point"])
        if near(p, want):
            break
        if prev is not None and near(p, prev):
            si += 1          # retry of the previous click
            continue
        break
    if si < len(man) and near(tuple(man[si]["point"]), want):
        resolved.append((rep, page, ok, man[si]["file"]))
        si += 1
    else:
        resolved.append((rep, page, ok, None))

matched = sum(1 for *_, f in resolved if f)
print(f"matched {matched}/{len(clicks)} clicks to shots")

def row_profile(path):
    im = np.asarray(Image.open(EYES.parent / path).convert("RGB"), dtype=float)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    red = (r > 170) & (g < 90) & (b < 90)          # crosshair pixels
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    lum[red] = np.nan
    prof = np.nanmean(lum, axis=1)                  # mean per row
    grad = np.abs(np.diff(prof))
    return prof, grad

C = 220        # crosshair centre row in the 440x440 crop

def boundaries(grad, c=C, min_prom=1.2, span=120):
    """Nearest strong gradient peaks above and below the centre."""
    up = down = None
    for k in range(1, span):
        yd = c + k
        if yd < len(grad) and grad[yd] > min_prom and (down is None or grad[yd] > grad[down]):
            if grad[yd] >= 2.0:
                down = yd if down is None or grad[yd] > grad[down] else down
        yu = c - k
        if yu >= 1 and grad[yu] > min_prom and (up is None or grad[yu] > grad[up]):
            if grad[yu] >= 2.0:
                up = yu if up is None or grad[yu] > grad[up] else up
    # simpler: strongest peak within 100px above and below
    up = int(np.argmax(grad[max(0, c - 100):c])) + max(0, c - 100)
    down = int(np.argmax(grad[c:c + 100])) + c
    return up, down

results = []
for rep, page, ok, f in resolved:
    if not f:
        continue
    prof, grad = row_profile(f)
    up, down = boundaries(grad)
    height = down - up if down and up else None
    # contrast inside the row vs the gap above: icon/label present?
    inside = prof[up + 5:down - 5]
    contrast = float(np.nanstd(inside)) if len(inside) > 4 else 0.0
    results.append((rep, page, ok, f, up, down, height, contrast))

ok_h = [h for r_, p_, ok, *_ , h, _c in [(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7]) for x in results] if ok and h]
fail_h = [x[6] for x in results if not x[2] and x[6]]
print(f"\nrow height at crosshair (button ~48px):")
print(f"  OK   clicks: median {np.median(ok_h):.0f}px (n={len(ok_h)})")
print(f"  FAIL clicks: median {np.median(fail_h):.0f}px (n={len(fail_h)})")

print("\nFAIL clicks detail (up/down = row boundary rows, centre=220):")
for rep, page, ok, f, up, down, h, contrast in results:
    if not ok:
        print(f"  rep{rep} {page:<14} up={up} down={down} h={h} contrast_inside={contrast:.1f} {f.split('/')[-1]}")

print("\nOK clicks detail:")
for rep, page, ok, f, up, down, h, contrast in results[:8]:
    if ok:
        print(f"  rep{rep} {page:<14} up={up} down={down} h={h} contrast_inside={contrast:.1f} {f.split('/')[-1]}")
