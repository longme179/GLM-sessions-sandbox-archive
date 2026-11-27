#!/usr/bin/env bash
# S2 A-side: same s2 "all" x3 reps + eyes, on the p-main tree (pre-change main).
set -u
cd ~/.cache/lme-perf/rv2/repo/scripts/perf || exit 1
export WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/1000
python3 run.py --tree ~/.cache/lme-perf/rv2/p-main --label s2-aside-a --budget 420 --max-seconds 240 --eyes -- \
  warmup:rounds=1 s2:variants=all,reps=3 2>&1 | tail -12
echo "EXIT=$?"
