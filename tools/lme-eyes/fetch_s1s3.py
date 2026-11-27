#!/usr/bin/env python3
"""Fetch the newest host run of each label into download/perf-responsive-v2/runs/<label>/.

Usage: python3 -I fetch_s1s3.py <label> [<label> ...]
Each run comes from ~/.cache/lme-perf/rv2/runs/<newest>-<label> on the host (summaries, records,
meta, inject log, probe logs, and the eyes when the run has them), sha256-verified on the way.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile

sys.path.insert(0, "/home/z/my-project/scripts")
from host_run import run  # noqa: E402

HOST = "/home/kimhoanglong/.cache/lme-perf/rv2/runs"
LOCAL = "/home/z/my-project/download/perf-responsive-v2/runs"
labels = sys.argv[1:]
rc, text = run("cd %s && for l in %s; do echo \"RUN $l $(ls -dt *-$l 2>/dev/null | head -1)\"; done; "
               "echo EYES_BEGIN; ls -d */eyes 2>/dev/null; echo EYES_END" % (HOST, " ".join(labels)), 150, "/")
runs = dict(re.findall(r"RUN (\S+) (\S+)", text))
listing = text.split("EYES_BEGIN")[-1].split("EYES_END")[0] if "EYES_BEGIN" in text else ""
eyes_dirs = {name for name in re.findall(r"(\S+)/eyes", listing) if name != "*"}
print("host runs:", runs, "| with eyes:", sorted(eyes_dirs))
os.makedirs(LOCAL, exist_ok=True)
for label in labels:
    name = runs.get(label)
    if not name:
        print(f"{label}: no run on the host")
        continue
    paths = [f"{name}/summary.md", f"{name}/summary.json", f"{name}/records.json", f"{name}/meta.json",
             f"{name}/inject.log", f"{name}/probe"]
    if name in eyes_dirs:
        paths.append(f"{name}/eyes")
    scratch = f"{LOCAL}/_x"
    shutil.rmtree(scratch, ignore_errors=True)
    tgz = f"{LOCAL}/{label}.tgz"
    out = subprocess.run([sys.executable, "/home/z/my-project/scripts/host_fetch.py", HOST, tgz,
                          "--timeout", "300"] + sum([["--path", p] for p in paths], []),
                         capture_output=True, text=True).stdout.strip()
    print(f"{label}: {name} -> {out[-90:]}")
    if not os.path.exists(tgz):
        continue
    os.makedirs(scratch)
    with tarfile.open(tgz) as tar:
        try:
            tar.extractall(scratch, filter="data")
        except TypeError:
            tar.extractall(scratch)
    if name not in os.listdir(scratch):
        print(f"{label}: {name} not at the top of the tarball:", os.listdir(scratch)[:6])
        continue
    target = f"{LOCAL}/{label}"
    shutil.rmtree(target, ignore_errors=True)
    shutil.move(f"{scratch}/{name}", target)
    shutil.rmtree(scratch, ignore_errors=True)
    size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(target) for f in fs)
    print(f"{label}: {sum(len(fs) for _, _, fs in os.walk(target))} files, {size // 1024} KB")
    manifest = f"{target}/eyes/manifest.json"
    if os.path.exists(manifest):
        data = json.load(open(manifest))
        first = data[:1] if isinstance(data, list) else {k: (v[:1] if isinstance(v, list) else v) for k, v in data.items()}
        print("  manifest:", type(data).__name__, len(data), json.dumps(first)[:500])
        files = sorted(os.listdir(f"{target}/eyes"))
        print("  eyes files:", len(files), files[:3])
