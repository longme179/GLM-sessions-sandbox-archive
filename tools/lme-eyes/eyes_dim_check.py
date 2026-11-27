#!/usr/bin/env python3
"""Are the swallowed clicks falling on a DIMMED nav list?

S2's symptom is a page stuck dimmed mid-animation (recede cue never restored). If the
same dim state also swallows clicks, the FAIL shots' row band under the crosshair
should be measurably darker than the OK shots' band for the SAME page.

elements is the perfect control: OK in rep0 (001), FAIL in rep1 (022) and rep2 (045).
Compare mean luminance of the row band (the 47-55px band found around y=220) between
the OK and the FAIL shots, for every page that has both outcomes.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

RUN = Path("/home/z/my-project/work/vision/s2vision2")
EYES = RUN / "eyes"
d = json.load(open(RUN / "records.json"))
trace = d["meta"]["nav_trace"]
clicks = []
for r in d["records"]:
    if r.get("scenario") != "s2" or r.get("variant") != "all":
        continue
    for p in r.get("pages") or []:
        if p.get("unreachable"):
            continue
        clicks.append((r["rep"], p["page"], p.get("ok")))

def near(a, b, tol=2):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol

man = [r for r in json.load(open(EYES / "manifest.json")) if r.get("file", "").endswith(".jpg")]
si = 0
resolved = []
for rep, page, ok in clicks:
    want = tuple(trace[len(resolved)]["point"])
    prev = tuple(trace[len(resolved) - 1]["point"]) if resolved else None
    while si < len(man):
        p = tuple(man[si]["point"])
        if near(p, want):
            break
        if prev and near(p, prev):
            si += 1
            continue
        break
    resolved.append((rep, page, ok, man[si]["file"] if si < len(man) and near(tuple(man[si]["point"]), want) else None))
    if si < len(man) and near(tuple(man[si]["point"]), want):
        si += 1

def band_stats(path, half=28):
    """Luminance of the horizontal band centred on the crosshair (row 220)."""
    im = np.asarray(Image.open(RUN / path).convert("RGB"), dtype=float)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    red = (r > 170) & (g < 90) & (b < 90)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    band = lum[220 - half:220 + half, 60:380]        # exclude side margins
    mask = ~red[220 - half:220 + half, 60:380]
    return float(band[mask].mean()), float(band[mask].std())

# group by page
by_page = {}
for rep, page, ok, f in resolved:
    if f:
        by_page.setdefault(page, []).append((rep, ok, f))

print(f"{'page':<15} {'OK lum (n)':<16} {'FAIL lum (n)':<16} delta")
both = 0
for page, rows in by_page.items():
    oks = [band_stats(f) for rep, ok, f in rows if ok]
    fails = [band_stats(f) for rep, ok, f in rows if not ok]
    if not oks or not fails:
        continue
    both += 1
    om = np.mean([m for m, _ in oks])
    fm = np.mean([m for m, _ in fails])
    print(f"{page:<15} {om:7.1f} ({len(oks)})    {fm:7.1f} ({len(fails)})    {fm - om:+6.1f}")

# Same-page pair detail: elements
print("\nelements pair (OK rep0 vs FAIL rep1/rep2):")
for rep, ok, f in by_page["elements"]:
    m, s = band_stats(f)
    print(f"  rep{rep} {'OK ' if ok else 'FAIL'} mean={m:.1f} std={s:.1f} {f}")
print("keybinds (FAIL all reps):")
for rep, ok, f in by_page["keybinds"]:
    m, s = band_stats(f)
    print(f"  rep{rep} {'OK ' if ok else 'FAIL'} mean={m:.1f} std={s:.1f} {f}")
print("controlLayout (OK all reps):")
for rep, ok, f in by_page["controlLayout"]:
    m, s = band_stats(f)
    print(f"  rep{rep} {'OK ' if ok else 'FAIL'} mean={m:.1f} std={s:.1f} {f}")
