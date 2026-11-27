#!/usr/bin/env python3
"""Map each eye shot to its s2 page click, and pair failing pages with their photos.

The manifest gives capture order; records.json gives rep/page order and outcomes.
The click order in the "all" variant follows the pages list, one click per page
(nav scroll shots are not clicks; every eyes/*.jpg tagged click-* is one).
"""
import json
from pathlib import Path

RUN = Path("/home/z/my-project/work/vision/s2vision2")
d = json.load(open(RUN / "records.json"))
man = json.load(open(RUN / "eyes" / "manifest.json"))

# The per-page click shots, in order, across all reps
shots = [r for r in man if r.get("file", "").endswith(".jpg")]
print(f"{len(shots)} jpg shots")

# s2 "all" rep clicks = one per page entry (pages list order), skipping unreachable
page_clicks = []          # (rep, page, ok, react_ms, page_ms)
for r in d["records"]:
    if r.get("scenario") != "s2" or r.get("variant") != "all":
        continue
    for p in r.get("pages") or []:
        if p.get("unreachable"):
            continue
        page_clicks.append((r["rep"], p["page"], p.get("ok"), p.get("react_ms"), p.get("page_ms")))

print(f"{len(page_clicks)} page clicks recorded")
# shots beyond the page clicks are S2 close/recovery clicks etc.
pairs = []
for i, (rep, page, ok, react, page_ms) in enumerate(page_clicks):
    if i < len(shots):
        pairs.append((shots[i], rep, page, ok, react, page_ms))

# print the mapping for failing pages (and the first click of each rep for reference)
for shot, rep, page, ok, react, page_ms in pairs:
    mark = "OK " if ok else "FAIL"
    print(f"rep{rep} {mark} {page:<14} react={react} page_ms={page_ms} -> {shot['file']} point={shot['point']}")
