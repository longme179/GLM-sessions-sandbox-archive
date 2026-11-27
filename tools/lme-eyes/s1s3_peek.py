#!/usr/bin/env python3
"""Dump an S1/S3 run: per-rep timings, per-click outcomes, recoveries. Usage: s1s3_peek.py <run dir>"""
import json
import sys

run = sys.argv[1]
d = json.load(open(f"{run}/records.json"))
m = d["meta"]
print("specs:", json.dumps(m.get("specs_done")))
print("truncated:", m.get("truncated"), "| ended:", m.get("ended"), "| eyes:", m.get("eyes"))
print("problems:")
for p in d.get("problems") or []:
    print("   ", json.dumps(p)[:260])
for r in d["records"]:
    if r["scenario"] == "s1":
        cl = r.get("clicks") or []
        reacts = r.get("react_ms")
        print(f"\nS1 {r['variant']} rep{r['rep']} ok={r.get('ok')} tabs={r.get('tabs')} clicks={len(cl)} "
              f"duration={r.get('duration_ms')} final_settle={r.get('final_settle_ms')} close={r.get('close_ms')} "
              f"recovery={r.get('close_recovery')} stalls={len(r.get('stalls') or [])} ping={r.get('ping_ms')}")
        if r["variant"] == "ordered":
            for c in cl:
                print(f"    {c['tab']:<14} select={c.get('select_ms')} react={c.get('react_ms')} page={c.get('page_ms')} "
                      f"settle={c.get('settle_ms')} frame={c.get('frame_ms')}")
        else:
            print("    tabs    :", [c["tab"] for c in cl])
            print("    react_ms:", reacts)
            print("    select  :", r.get("select_ms"))
            gaps = [round(cl[i + 1]["t"] - cl[i]["t"]) for i in range(len(cl) - 1)]
            print("    gaps ms :", gaps[:14], "..." if len(gaps) > 14 else "")
            print("    first click -> last click ms:", round(cl[-1]["t"] - cl[0]["t"]) if cl else None)
        big = sorted(r.get("stalls") or [], reverse=True)[:6]
        print("    biggest stalls:", big)
    elif r["scenario"] == "s3":
        print(f"\nS3 rep{r['rep']} steps={len(r.get('steps') or [])} stalls={len(r.get('stalls') or [])} ping={r.get('ping_ms')} "
              f"workspace={json.dumps(r.get('workspace'))[:160]} final_open={r.get('final_open')}")
        t0 = None
        for s in r.get("steps") or []:
            print(f"    {s['panel']:<14} dwell={s['dwell_ms']} open={s.get('open_ms')} esc->gone={s.get('close_ms')} "
                  f"gone={s.get('gone_ms')} closed={s.get('closed')} recovery={s.get('recovery')} "
                  f"stalls_open={s.get('stalls_open')} stalls_close={s.get('stalls_close')}")
        big = sorted(r.get("stalls") or [], reverse=True)[:8]
        print("    biggest stalls:", big)
print("\nmeta: still_reads / s1_tab_rects")
sr = m.get("still_reads") or []
print("  still_reads:", len(sr), "reads:", sorted({e["reads"] for e in sr}),
      "moved_px max:", max([e["moved_px"] for e in sr], default=None))
for e in sr:
    if e["reads"] > 2 or e["moved_px"] > 0.5:
        print("    moved:", e)
for entry in m.get("s1_tab_rects") or []:
    print("  t=%.0f" % entry["t"], {tab: (round(v.get("x", 0), 1), round(v.get("y", 0), 1), v.get("w"), v.get("h"))
                                 for tab, v in entry["rects"].items()})
print("\ninject.log tail:")
lines = open(f"{run}/inject.log").read().splitlines()
print("   lines:", len(lines))
for line in lines[-6:]:
    print("   ", line[:200])
