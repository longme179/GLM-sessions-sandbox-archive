#!/usr/bin/env python3
"""Do the eyes crops of an S1 run show a tab button under the crosshair?

Usage: python3 -I eyes_tabs_check.py <run dir>
Two checks per crop (the click in the middle of the crop):
  - the click point of the manifest against the tab rects the harness read for its rep
    (meta.s1_tab_rects, x/y = centre): which button holds it, how many px from each edge;
  - the pixels: the colour is followed from the click to the four sides until it changes. A tab
    button is 287-288 x 40 px, so a click in its middle keeps the colour for about 143 px left and
    right and 20 px up and down.
"""
import json
import os
import sys

from PIL import Image

run = sys.argv[1]
records = json.load(open(f"{run}/records.json"))
tabs = {}
for entry in records["meta"].get("s1_tab_rects") or []:
    for tab, rect in entry["rects"].items():
        tabs[tab] = rect
print("tab rects, top-left and size (px):")
for tab, r in tabs.items():
    print(f"  {tab:<14} x={r['x'] - r['w'] / 2:7.1f} y={r['y'] - r['h'] / 2:6.1f} {round(r['w'])}x{round(r['h'])}")

manifest = json.load(open(f"{run}/eyes/manifest.json"))
shots = []
if isinstance(manifest, list):
    shots = manifest
else:
    for key, value in manifest.items():
        if isinstance(value, list):
            shots = value
            break
        if isinstance(value, dict):
            shots = [dict(v, file=k) if isinstance(v, dict) else {"file": k, "value": v} for k, v in value.items()]
            break
print("manifest:", type(manifest).__name__, "shots:", len(shots))
if shots:
    print("first shot:", json.dumps(shots[0])[:300])


def point_of(shot):
    if not isinstance(shot, dict):
        return None
    for kx, ky in (("x", "y"), ("cx", "cy"), ("click_x", "click_y"), ("sx", "sy")):
        if isinstance(shot.get(kx), (int, float)) and isinstance(shot.get(ky), (int, float)):
            return float(shot[kx]), float(shot[ky])
    return None


def holder(x, y):
    for tab, r in tabs.items():
        if abs(x - r["x"]) <= r["w"] / 2 and abs(y - r["y"]) <= r["h"] / 2:
            return tab, (round(r["w"] / 2 - (x - r["x"]), 1), round(r["w"] / 2 + (x - r["x"]), 1),
                         round(r["h"] / 2 - (y - r["y"]), 1), round(r["h"] / 2 + (y - r["y"]), 1))
    return None, None


def red(px):
    return px[0] > 170 and px[1] < 110 and px[2] < 110


def extent(px, cx, cy, dx, dy, size):
    def warm(q):  # the red crosshair and its anti-aliased edge
        return q[0] - max(q[1], q[2]) > 40

    start = 6
    while start < 150 and warm(px[cx + dx * start, cy + dy * start]):
        start += 1
    ref = px[cx + dx * start, cy + dy * start]
    step = 0
    while True:
        x, y = cx + dx * (start + step + 1), cy + dy * (start + step + 1)
        if not (0 <= x < size[0] and 0 <= y < size[1]):
            break
        q = px[x, y]
        if warm(q):  # the crosshair is drawn over the button: step over it
            step += 1
            continue
        if max(abs(q[0] - ref[0]), abs(q[1] - ref[1]), abs(q[2] - ref[2])) > 28:
            break
        step += 1
    return start + step


files = sorted(f for f in os.listdir(f"{run}/eyes") if not f.endswith(".json"))
print("crop files:", len(files)
      and files[:2], "...", files[-1:] if files else "")
rows = []
for index, shot in enumerate(shots):
    name = next((shot[k] for k in ("file", "path", "image", "jpg", "png")
                 if isinstance(shot, dict) and isinstance(shot.get(k), str) and shot.get(k)), None)
    path = os.path.join(run, name) if name else (f"{run}/eyes/{files[index]}" if index < len(files) else None)
    if not path or not os.path.exists(path):
        rows.append((index, name, "missing"))
        continue
    image = Image.open(path).convert("RGB")
    px, size = image.load(), image.size
    if isinstance(shot, dict) and isinstance(shot.get("point"), (list, tuple)) and len(shot["point"]) == 2:
        shot = dict(shot, x=shot["point"][0], y=shot["point"][1])  # the manifest keeps the click in "point"
    point = point_of(shot)
    crop = shot.get("crop") if isinstance(shot, dict) else None
    # the crop is 440x440 around the click unless a screen edge clipped it: follow the click itself
    cx, cy = (int(point[0] - crop[0]), int(point[1] - crop[1])) if crop and point else (size[0] // 2, size[1] // 2)
    sides = [extent(px, cx, cy, dx, dy, size) for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))]
    tab, margins = holder(*point) if point else (None, None)
    rows.append((index, os.path.basename(path), size, sides, point, tab, margins))

inside = on_button = 0
for row in rows:
    if row[2] == "missing":
        print(row)
        continue
    index, name, size, (left, right, up, down), point, tab, margins = row
    if tab:
        inside += 1
    if min(left, right) >= 100 and min(up, down) >= 18:
        on_button += 1
    where = f"{point[0]:.0f},{point[1]:.0f}" if point else "no point in the manifest"
    print(f"  #{index:<3} {name:<18} {where:<12} colour stays L/R/U/D {left:3d} {right:3d} {up:3d} {down:3d}"
          f"   button: {tab or '-'} margins(left,right,top,bottom)={margins}")
print(f"crops: {len(rows)}; click point inside a tab rect: {inside}; colour run of a button middle "
      f"(>=100 px sideways, >=18 px up/down): {on_button}")
