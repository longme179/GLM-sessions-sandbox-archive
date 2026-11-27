#!/usr/bin/env python3
"""S2 "all" x3 reps with the eyes on, run on two trees (A = main, B = branch): same clicks, same outcomes?

Usage: eyes_ab_compare.py <runA dir> <runB dir> [--out report.txt]
Each dir holds records.json and eyes/ (manifest.json + crops) fetched from the host.
Everything printed here is computed from those files; nothing is typed in by hand.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

C = 220          # crosshair centre row (and column) of a 440x440 crop
OUT = []


def say(text=""):
    OUT.append(text)
    print(text)


def load(run):
    d = json.load(open(run / "records.json"))
    trace = d["meta"].get("nav_trace") or []
    reps = []
    for r in d["records"]:
        if r.get("scenario") != "s2" or r.get("variant") != "all":
            continue
        pages = [p for p in (r.get("pages") or []) if not p.get("unreachable")]
        reps.append({"rep": r["rep"], "ok": r.get("ok"), "pages": pages, "stalls": r.get("stalls") or []})
    reps.sort(key=lambda r: r["rep"])
    return d, trace, reps


def clicks_of(reps, trace):
    """One row per page click, in click order, zipped with its nav_trace entry."""
    rows = []
    for r in reps:
        for p in r["pages"]:
            tr = trace[len(rows)]
            assert tr["key"] == p["page"], (tr["key"], p["page"])
            rows.append({"rep": r["rep"], **p, "trace": tr})
    assert len(rows) == len(trace), (len(rows), len(trace))
    return rows


def near(a, b, tol=2):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def match_shots(run, rows):
    """Eyes shot of every click. Shots are the click_at calls in order; a flagged retry
    repeats the previous click's point, so a shot at the PREVIOUS point is that retry."""
    man = [r for r in json.load(open(run / "eyes" / "manifest.json")) if r.get("file", "").endswith(".jpg")]
    si = 0
    for i, row in enumerate(rows):
        want = tuple(row["trace"]["point"])
        prev = tuple(rows[i - 1]["trace"]["point"]) if i else None
        while si < len(man):
            p = tuple(man[si]["point"])
            if near(p, want):
                break
            if prev is not None and near(p, prev):
                si += 1
                continue
            break
        if si < len(man) and near(tuple(man[si]["point"]), want):
            row["shot"] = man[si]["file"]
            si += 1
        else:
            row["shot"] = None
    return len(man)


def lum_of(run, rel):
    """Luminance of a crop with the red crosshair masked out (NaN)."""
    im = np.asarray(Image.open(run / rel).convert("RGB"), dtype=float)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    red = (r > 170) & (g < 90) & (b < 90)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    lum[red] = np.nan
    return lum


def row_shape(lum):
    """Strongest brightness step above and below the centre row: the button row's edges."""
    prof = np.nanmean(lum, axis=1)
    grad = np.abs(np.diff(prof))
    up = int(np.nanargmax(grad[max(0, C - 100):C])) + max(0, C - 100)
    down = int(np.nanargmax(grad[C:C + 100])) + C
    band = lum[C - 28:C + 28, 60:380]
    return up, down, down - up, float(np.nanmean(band)), float(np.nanstd(band))


def stats(values):
    v = np.array([x for x in values if x is not None], dtype=float)
    if not len(v):
        return "-"
    return f"{np.median(v):.1f} / {np.percentile(v, 95):.1f} / {v.max():.1f} (n={len(v)})"


def stall_stats(stalls):
    ms = np.array([s[0] for s in stalls], dtype=float)
    if not len(ms):
        return "none"
    return (f"{int((ms > 33).sum())} >33ms, {int((ms > 100).sum())} >100ms, {int((ms > 300).sum())} >300ms, "
            f"max {ms.max():.0f}ms, total {ms.sum():.0f}ms")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--out")
    a = ap.parse_args()
    A, B = Path(a.run_a), Path(a.run_b)
    dA, trA, repsA = load(A)
    dB, trB, repsB = load(B)
    rowsA, rowsB = clicks_of(repsA, trA), clicks_of(repsB, trB)

    say("S2 A/B - variant all, 3 reps, eyes on (computed from records.json + eyes/)")
    for name, d, run in (("A (main)", dA, A), ("B (branch)", dB, B)):
        say(f"  {name:<10} {d['meta'].get('ended')}, eyes {d['meta'].get('eyes')}, problems {len(d.get('problems') or [])}, dir {run.name}")
    say()

    # 1. outcomes per rep
    say("1. Outcome per page and rep (o = settled, x = swallowed / not settled)")
    pages = [p["page"] for p in repsA[0]["pages"]]
    assert pages == [p["page"] for p in repsB[0]["pages"]], "the two runs did not click the same pages"
    say(f"  {'page':<15}" + "".join(f"{'A r' + str(r['rep']):^8}" for r in repsA) + " " + "".join(f"{'B r' + str(r['rep']):^8}" for r in repsB))
    tables = {}
    for side, reps in (("A", repsA), ("B", repsB)):
        tables[side] = {(p["page"], r["rep"]): (bool(p.get("ok")), tuple(p.get("failed_checks") or []))
                        for r in reps for p in r["pages"]}
    for page in pages:
        cells = [("o" if tables[s][(page, r["rep"])][0] else "x") for s, reps in (("A", repsA), ("B", repsB)) for r in reps]
        say(f"  {page:<15}" + "".join(f"{c:^8}" for c in cells))
    say()
    for name, reps in (("A (main)", repsA), ("B (branch)", repsB)):
        tot = sum(1 for r in reps for p in r["pages"] if not p.get("ok"))
        per = [sum(1 for p in r["pages"] if not p.get("ok")) for r in reps]
        say(f"  {name:<10} violations {tot}/{sum(len(r['pages']) for r in reps)}  per rep {per}")
    say()
    say("  Pages violated on A but not B, and on B but not A (same rep):")
    both = only_a = only_b = 0
    for rep in (r["rep"] for r in repsA):
        for page in pages:
            ok_a, chk_a = tables["A"][(page, rep)]
            ok_b, chk_b = tables["B"][(page, rep)]
            va, vb = (not ok_a), (not ok_b)
            if va and vb:
                both += 1
                same = "same checks" if chk_a == chk_b else f"checks differ A={list(chk_a)} B={list(chk_b)}"
                say(f"    rep{rep} {page:<15} violated on both ({same})")
            elif va:
                only_a += 1
                say(f"    rep{rep} {page:<15} violated on A only {list(chk_a)}")
            elif vb:
                only_b += 1
                say(f"    rep{rep} {page:<15} violated on B only {list(chk_b)}")
    say(f"  => both {both}, A only {only_a}, B only {only_b}")
    say()

    # 2. latencies (ms: median / p95 / max)
    say("2. Latency in ms (median / p95 / max): click -> first frame, click -> page built/present, click -> settled")
    for name, rows in (("A (main)", rowsA), ("B (branch)", rowsB)):
        say(f"  {name:<10} frame {stats([r.get('frame_ms') for r in rows])}")
        say(f"  {'':<10} built  {stats([r.get('page_ms') for r in rows])}")
        say(f"  {'':<10} settle(all) {stats([r.get('settle_ms') for r in rows])}")
        say(f"  {'':<10} settle(ok)   {stats([r.get('settle_ms') for r in rows if r.get('ok')])}")
    say()
    say("  GUI-thread stalls during the S2 reps (heartbeat of the shell process):")
    for name, reps in (("A (main)", repsA), ("B (branch)", repsB)):
        for r in reps:
            say(f"    {name:<10} rep{r['rep']}: {stall_stats(r['stalls'])}")
        say(f"    {name:<10} all  : {stall_stats([s for r in reps for s in r['stalls']])}")
    say()

    # 3. rect check: was the click on the delegate the probe last saw?
    say("3. Click point vs the delegate rect of its last nav read (window px; rect centre x,y, size w x h)")
    for name, rows in (("A (main)", rowsA), ("B (branch)", rowsB)):
        cnt = {"ok_in": 0, "ok_out": 0, "fail_in": 0, "fail_out": 0}
        dys, edges = [], []
        for r in rows:
            tr = r["trace"]
            last = tr["reads"][-1]
            x, y, w, h = last["x"], last["y"], last["w"], last["h"]
            wx, wy = tr["point"][0] - tr["box"][0], tr["point"][1] - tr["box"][1]
            inside = (x - w / 2) <= wx <= (x + w / 2) and (y - h / 2) <= wy <= (y + h / 2)
            key = ("ok_" if r.get("ok") else "fail_") + ("in" if inside else "out")
            cnt[key] += 1
            if not r.get("ok"):
                dys.append(wy - y)
                edges.append(min(abs(wy - (y - h / 2)), abs((y + h / 2) - wy)))
        say(f"  {name:<10} OK inside={cnt['ok_in']} outside={cnt['ok_out']}; "
            f"FAIL inside={cnt['fail_in']} outside={cnt['fail_out']}; "
            f"FAIL dy from rect centre median {np.median(dys):+.1f}px (max |dy| {np.max(np.abs(dys)):.1f}), "
            f"distance to the nearest edge median {np.median(edges):.1f}px (min {np.min(edges):.1f})")
    say()

    # 4. the eyes: what was under the crosshair when the click landed
    nA, nB = match_shots(A, rowsA), match_shots(B, rowsB)
    say(f"4. Eyes: {nA} shots in A, {nB} in B; clicks matched to a shot: "
        f"A {sum(1 for r in rowsA if r['shot'])}/{len(rowsA)}, B {sum(1 for r in rowsB if r['shot'])}/{len(rowsB)}")
    say("   Row under the crosshair: strongest brightness edges above/below the centre (button ~48 px).")
    for name, rows, run in (("A (main)", rowsA, A), ("B (branch)", rowsB, B)):
        heights = {"ok": [], "fail": []}
        say(f"  {name}")
        for r in rows:
            if not r["shot"]:
                continue
            up, down, h, mean, std = row_shape(lum_of(run, r["shot"]))
            r["shape"] = (up, down, h, mean, std)
            heights["ok" if r.get("ok") else "fail"].append(h)
        for k in ("ok", "fail"):
            v = np.array(heights[k], dtype=float)
            say(f"    {k:<4} clicks: row height median {np.median(v):.0f}px (min {v.min()}, max {v.max()}, n={len(v)})")
    say("   Every swallowed click:")
    for name, rows, run in (("A (main)", rowsA, A), ("B (branch)", rowsB, B)):
        say(f"  {name}")
        for r in rows:
            if r.get("ok") or not r["shot"]:
                continue
            up, down, h, mean, std = r["shape"]
            tr = r["trace"]
            say(f"    rep{r['rep']} {r['page']:<15} edges up={up - C:+d} down={down - C:+d} (h={h}px, "
                f"rect h={tr['reads'][-1]['h']}) band mean={mean:.1f} std={std:.1f} {Path(r['shot']).name}")
    say()

    # 5. same click on A and on B: is the picture the same?
    say("5. Same (rep, page) on A and on B: crop difference, mean |dLum| over the pixels (0 = identical picture)")
    diffs, same_pic, same_shape = [], 0, 0
    worst = []
    for ra, rb in zip(rowsA, rowsB):
        assert (ra["rep"], ra["page"]) == (rb["rep"], rb["page"])
        if not (ra["shot"] and rb["shot"]):
            continue
        la, lb = lum_of(A, ra["shot"]), lum_of(B, rb["shot"])
        d = np.abs(la - lb)
        m = float(np.nanmean(d))
        diffs.append(m)
        same_pic += m < 0.5
        same_shape += ra["shape"][2] == rb["shape"][2]
        worst.append((m, ra["rep"], ra["page"], bool(ra.get("ok")), bool(rb.get("ok"))))
    worst.sort(reverse=True)
    v = np.array(diffs)
    say(f"  pairs {len(v)}: mean |dLum| median {np.median(v):.2f}, p95 {np.percentile(v, 95):.2f}, max {v.max():.2f}; "
        f"pictures within 0.5 of identical: {same_pic}; same row height: {same_shape}")
    say("  Most different pairs (|dLum|, rep, page, ok A, ok B):")
    for m, rep, page, oa, ob in worst[:8]:
        say(f"    {m:6.2f}  rep{rep} {page:<15} A={'o' if oa else 'x'} B={'o' if ob else 'x'}")
    say("  Swallowed on both sides - A vs B band mean/std at the crosshair:")
    for ra, rb in zip(rowsA, rowsB):
        if ra.get("ok") or rb.get("ok") or not (ra["shot"] and rb["shot"]):
            continue
        say(f"    rep{ra['rep']} {ra['page']:<15} A {ra['shape'][3]:.1f}/{ra['shape'][4]:.1f} h={ra['shape'][2]}   "
            f"B {rb['shape'][3]:.1f}/{rb['shape'][4]:.1f} h={rb['shape'][2]}")
    if a.out:
        Path(a.out).write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
