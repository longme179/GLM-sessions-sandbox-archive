#!/usr/bin/env bash
# s2-vision run, THIS TIME from the repo checkout (current harness code), tree p-head.
set -u
cd ~/.cache/lme-perf/rv2/repo/scripts/perf || exit 1
export WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/1000
python3 run.py --tree ~/.cache/lme-perf/rv2/p-head --label s2-vision2 --budget 420 --max-seconds 240 --eyes -- \
  warmup:rounds=1 s2:variants=all,reps=3 2>&1 | tail -14
echo "EXIT=$?"
