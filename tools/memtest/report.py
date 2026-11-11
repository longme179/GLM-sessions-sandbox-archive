#!/usr/bin/env python3
"""report.py — aggregate scenario JSONs into the baseline report (memtest).

Reads results/<SCENARIO>#<run>.json files written by scenario.py /
gui_scenario.py / scenario_env.py, groups them by scenario, and emits
results/<out>.md: a median [min–max] table compared against the v1.9.3
report reference values with per-scenario tolerance verdicts (§15.4).

STANDALONE tool (policy Q8): never commit this into the Minewrap app repo.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics
import subprocess
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))

# Reference values — v1.9.3 report §13.1/§13.2 (Fedora 44, 12 cores,
# release build). Tolerances per report §15.4 (SR uses S3's ±0.3 —
# running-state, not listed separately there).
REF = {
    "S0":  dict(rss=5.56, pss=3.30, uss=3.27, threads=13, procs=1, tol=0.20),
    "S1":  dict(rss=6.31, pss=4.04, uss=4.01, threads=13, procs=1, tol=0.20),
    "S3":  dict(rss=6.48, pss=4.24, uss=4.21, threads=13, procs=1, tol=0.30),
    "SR":  dict(rss=6.51, pss=4.19, uss=4.16, threads=13, procs=1, tol=0.30),
    "SW":  dict(rss=7.43, pss=5.06, uss=5.03, threads=13, procs=1, tol=1.00),
    "SW2": dict(rss=5.43, pss=3.23, uss=3.21, threads=3,  procs=1, tol=0.20),
    "GUI": dict(rss=436.32, pss=195.60, uss=97.57, threads=87, procs=3,
                tol=10.00, tol_rss=30.00),
}
ORDER = ["S0", "S1", "S3", "SR", "SW", "SW2", "GUI"]
DESC = {
    "S0": "daemon + 0 instance",
    "S1": "daemon + 1 instance (offline)",
    "S3": "daemon + 3 instances (offline)",
    "SR": "S1 + instance đang chạy (stub burst 2000 + stream 0,5 s)",
    "SW": "SR + 1 client WS console (backfill + stream)",
    "SW2": "S0 nhưng TOKIO_WORKER_THREADS=2 (thí nghiệm D1)",
    "GUI": "cây minewrap-tauri (3 tiến trình, idle Dashboard)",
}


def load_scenarios(results_dir: str) -> dict:
    out: dict[str, list[dict]] = {}
    for path in sorted(glob.glob(os.path.join(results_dir, "*.json"))):
        base = os.path.basename(path)[:-5]
        m = re.match(r"^([A-Z0-9]+)#(\d+)$", base)
        if not m:
            continue
        scen, run = m.group(1), int(m.group(2))
        if scen not in REF:
            continue
        with open(path) as f:
            data = json.load(f)
        data["_run"] = run
        out.setdefault(scen, []).append(data)
    return out


def med(vals):
    return statistics.median(vals) if vals else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", default=os.path.join(HERE, "results"))
    ap.add_argument("--out", default="baseline-v1.9.3.md")
    ap.add_argument("--title", default="Baseline v1.9.3 — tái đo bằng harness memtest")
    args = ap.parse_args()

    scenarios = load_scenarios(args.results)
    lines = []
    lines.append(f"# {args.title}")
    lines.append("")
    try:
        uname = subprocess.run(["uname", "-srmo"], capture_output=True,
                               text=True).stdout.strip()
    except OSError:
        uname = "?"
    lines.append(f"- Ngày đo: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- Máy đo: `{uname}` (ncores = {os.cpu_count()})")
    lines.append("- Phương pháp: report v1.9.3 §12.2 — sampler cây process 1 Hz, "
                 "`smaps_rollup` (RSS/PSS/USS/Swap), loại subtree stub theo cmdline "
                 "marker `fakejava`; median [min–max] mỗi kịch bản.")
    lines.append("- Ngưỡng so khớp §15.4: S0/S1/SW2 ±0,2 · S3/SR ±0,3 · SW ±1,0 · "
                 "GUI ±10 PSS / ±30 RSS (MiB). PASS = |Δ median PSS| (GUI: cả RSS) "
                 "trong ngưỡng.")
    lines.append("")
    lines.append("| Kịch bản | runs | RSS | PSS | USS | threads | procs | "
                 "PSS ref | ΔPSS | Verdict |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")

    verdicts = {}
    for scen in ORDER:
        runs = scenarios.get(scen)
        if not runs:
            lines.append(f"| **{scen}** — {DESC[scen]} | – | – | – | – | – | – | "
                         f"{REF[scen]['pss']:.2f} | – | MISSING |")
            verdicts[scen] = "MISSING"
            continue
        rss = med([r["median"]["rss"] for r in runs])
        pss = med([r["median"]["pss"] for r in runs])
        uss = med([r["median"]["uss"] for r in runs])
        thr = med([r["median"]["threads"] for r in runs])
        prc = med([r["median"]["procs"] for r in runs])
        rss_rng = (min(r["min"]["rss"] for r in runs), max(r["max"]["rss"] for r in runs))
        pss_rng = (min(r["min"]["pss"] for r in runs), max(r["max"]["pss"] for r in runs))
        ref = REF[scen]
        dpss = pss - ref["pss"]
        if scen == "GUI":
            ok = abs(dpss) <= ref["tol"] and abs(rss - ref["rss"]) <= ref["tol_rss"]
        else:
            ok = abs(dpss) <= ref["tol"]
        verdict = "PASS" if ok else "FAIL"
        verdicts[scen] = verdict
        lines.append(
            f"| **{scen}** — {DESC[scen]} | {len(runs)} | "
            f"{rss:.2f} [{rss_rng[0]:.2f}–{rss_rng[1]:.2f}] | "
            f"{pss:.2f} [{pss_rng[0]:.2f}–{pss_rng[1]:.2f}] | "
            f"{uss:.2f} | {thr:.0f} | {prc:.0f} | {ref['pss']:.2f} | "
            f"{dpss:+.2f} | **{verdict}** |")

    lines.append("")
    npass = sum(1 for v in verdicts.values() if v == "PASS")
    nmiss = sum(1 for v in verdicts.values() if v == "MISSING")
    lines.append(f"**Tổng: {npass} PASS / {len(ORDER) - nmiss} đo được"
                 + (f" ({nmiss} MISSING)" if nmiss else "") + ".**")
    lines.append("")
    lines.append("Ghi chú: số đo sandbox (Debian, 2 lõi) chỉ để xác minh cơ chế "
                 "harness — baseline chính thức phải đo trên máy user (Fedora 44, "
                 "12 lõi) theo plan v1.1 task A2. GUI scenario cần display (Wayland "
                 "session hoặc Xvfb).")
    out_path = os.path.join(args.results, args.out)
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"report: wrote {out_path}")
    for scen in ORDER:
        print(f"  {scen}: {verdicts[scen]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
