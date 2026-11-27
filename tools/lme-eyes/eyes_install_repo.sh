#!/usr/bin/env bash
# Install the eyes into the REPO checkout (the scripts sessions 3-4 actually ran),
# not the prepared tree (whose scripts are a stale 33c687c export).
set -u
R=~/.cache/lme-perf/rv2/repo/scripts/perf
T=~/.cache/lme-perf/rv2/p-head/scripts/perf
cd "$R" || exit 1

echo "== repo state before =="
git -C ~/.cache/lme-perf/rv2/repo status --short | head -5
git -C ~/.cache/lme-perf/rv2/repo log --oneline -1

echo "== install eyes.py =="
cp "$T/eyes.py" eyes.py && echo copied

python3 - <<'PYEOF' || exit 1
# scenarios.py: import + Ctx.eyes + click_at hook (anchors of the e5ef1b1 version)
src = open("scenarios.py").read()
if "import eyes" not in src:
    a = "from probe import ProbeError  # noqa: E402"
    assert a in src
    src = src.replace(a, a + "\nimport eyes  # noqa: E402  (screenshot eyes; off unless ctx.eyes is set)", 1)
if "self.eyes = None" not in src:
    a = "        self.box = None             # top-left of the Settings window on the output"
    assert a in src
    src = src.replace(a, a + "\n        self.eyes = None            # eyes.Eyes when a run wants a screenshot per click", 1)
if "self.eyes.look" not in src:
    a = '    def click_at(self, x, y):\n        return self.shot(self.inj.click_at(x, y))\n'
    assert a in src, "click_at anchor"
    b = ('    def click_at(self, x, y):\n'
         '        at = self.shot(self.inj.click_at(x, y))\n'
         '        if self.eyes is not None:\n'
         '            try:\n'
         '                self.eyes.look((x, y), tag=f"click-{x:.0f}-{y:.0f}")\n'
         '            except Exception:  # noqa: BLE001  (the eyes never fail a run)\n'
         '                pass\n'
         '        return at\n')
    src = src.replace(a, b, 1)
open("scenarios.py", "w").write(src)
print("scenarios.py patched")

# run.py: --eyes flag + import + ctx wiring + manifest dump
src = open("run.py").read()
if '"--eyes"' not in src:
    a = '    ap.add_argument("--no-notice", action="store_true", help="no desktop notification at the swap")'
    assert a in src, "flag anchor"
    src = src.replace(a, a + '\n    ap.add_argument("--eyes", action="store_true", '
                     'help="screenshot the screen around every click (eyes/ under the run dir)")', 1)
if "import eyes" not in src:
    a = "import scenarios\n"
    assert src.count(a) == 1, "import anchor"
    src = src.replace(a, a + "import eyes  # noqa: E402  (screenshot eyes, active only with --eyes)\n", 1)
if "ctx.eyes = eyes.Eyes" not in src:
    a = ('        ctx = scenarios.Ctx(inj, probe, deadline_ms=time.time() * 1000.0 + args.budget * 1000.0,\n'
         '                            width=screen["width"], height=screen["height"])')
    assert a in src, "ctx anchor"
    src = src.replace(a, a + '\n        if args.eyes:\n            ctx.eyes = eyes.Eyes(out, screen["width"], screen["height"])', 1)
if 'ctx.meta["eyes"]' not in src:
    a = '            ctx.meta["ended"] = failure or "finished"'
    assert a in src, "dump anchor"
    src = src.replace(a, a + '\n            if ctx.eyes is not None:\n                ctx.meta["eyes"] = len(ctx.eyes.dump())', 1)
open("run.py", "w").write(src)
print("run.py patched")
PYEOF

python3 -c "import ast; ast.parse(open('scenarios.py').read()); ast.parse(open('run.py').read()); print('ast OK')"
python3 run.py --help 2>&1 | grep -c "  --eyes" 
python3 run.py --simulate --eyes --out /tmp/smoke_repo_eyes -- s2:reps=1 2>&1 | tail -2
echo "== repo state after =="
git -C ~/.cache/lme-perf/rv2/repo status --short | head -8
