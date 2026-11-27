#!/usr/bin/env python3
"""S1 evidence, as anchored edits on the repo checkout (anchors of 08da4b7).

Run on the host from scripts/perf of the repo checkout:  python3 /tmp/s1s3_patch3_repo.py
Idempotent (the whole new text in the file means the edit is done); a drifted anchor stops
the script before anything is written.

Why: the owner watched the first runs and saw clicks that seemed to miss. For S2 the
nav_trace already says, per click, where the delegate was; S1 had nothing of the kind. Now
every S1 rep keeps the rect of each tab button as it was read for that rep
(meta.s1_tab_rects), so each click can be checked against the button it aimed at, and the
eyes crops (a screenshot per click) against those rects.
"""
import ast

CHANGED = []


def sub(src, old, new, note):
    if new in src:
        return src
    assert src.count(old) == 1, f"anchor not unique ({src.count(old)}x): {note}"
    CHANGED.append(note)
    return src.replace(old, new, 1)


src = open("scenarios.py").read()

src = sub(src,
          "        self.box = None             # top-left of the Settings window on the output\n",
          "        self.box = None             # top-left of the Settings window on the output\n"
          "        self.last_still_rect = None  # the rect still_item_point last settled on\n",
          "scenarios: Ctx.last_still_rect")

src = sub(src,
          "                self.meta.setdefault(\"still_reads\", []).append(\n"
          "                    {\"t\": round(self.now(), 3), \"item\": name, \"reads\": reads, \"moved_px\": round(moved, 2)})\n"
          "                return rect[\"x\"], rect[\"y\"]\n",
          "                self.meta.setdefault(\"still_reads\", []).append(\n"
          "                    {\"t\": round(self.now(), 3), \"item\": name, \"reads\": reads, \"moved_px\": round(moved, 2)})\n"
          "                self.last_still_rect = dict(rect)\n"
          "                return rect[\"x\"], rect[\"y\"]\n",
          "scenarios: still_item_point keeps the rect")

src = sub(src,
          "    rects = {}\n"
          "    for tab in tabs:\n"
          "        point = ctx.still_item_point(f\"perfTab_{tab}\")\n"
          "        if point is None:\n"
          "            ctx.escape(\"s1: the tab rects cannot be read\")\n"
          "            raise Skip(f\"perfTab_{tab} is not on screen or does not come to rest\")\n"
          "        rects[tab] = point\n"
          "    return rects\n",
          "    rects, seen = {}, {}\n"
          "    for tab in tabs:\n"
          "        point = ctx.still_item_point(f\"perfTab_{tab}\")\n"
          "        if point is None:\n"
          "            ctx.escape(\"s1: the tab rects cannot be read\")\n"
          "            raise Skip(f\"perfTab_{tab} is not on screen or does not come to rest\")\n"
          "        rects[tab] = point\n"
          "        seen[tab] = ctx.last_still_rect\n"
          "    ctx.meta.setdefault(\"s1_tab_rects\", []).append({\"t\": round(ctx.now(), 3), \"rects\": seen})\n"
          "    return rects\n",
          "scenarios: tab_points keeps every rect of the rep")

ast.parse(src)
open("scenarios.py", "w").write(src)

print("edits applied:" if CHANGED else "nothing to do (already patched)")
for note in CHANGED:
    print("  -", note)
