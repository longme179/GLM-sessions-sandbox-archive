#!/usr/bin/env bash
# S1 (Control Center tabs) and S3 (mixed panels) on one probe tree, from the repo checkout.
#   MODE=s1eyes : warm-up, s1 ordered+random x3 reps with the eyes on (a screenshot per click)
#   MODE=fast   : warm-up, s1 fast x3 reps without the eyes (nothing may slow the burst down)
#   MODE=s3     : warm-up, s3 x3 reps
# Env: TREE (probe tree), LABEL (run label), MODE.
set -u
cd ~/.cache/lme-perf/rv2/repo/scripts/perf || exit 1
export WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/1000
case "${MODE:?}" in
  s1eyes)
    python3 run.py --tree "${TREE:?}" --label "${LABEL:?}" --budget 300 --max-seconds 240 --eyes -- \
      warmup:rounds=1 "s1:variants=ordered+random,reps=3" 2>&1 | tail -16 ;;
  fast)
    python3 run.py --tree "${TREE:?}" --label "${LABEL:?}" --budget 240 --max-seconds 240 -- \
      warmup:rounds=1 "s1:variants=fast,reps=3" 2>&1 | tail -16 ;;
  s3)
    python3 run.py --tree "${TREE:?}" --label "${LABEL:?}" --budget 330 --max-seconds 240 -- \
      warmup:rounds=1 s3:reps=3 2>&1 | tail -16 ;;
  *) echo "unknown MODE"; exit 2 ;;
esac
echo "EXIT=${PIPESTATUS[0]}"
date
ls -dt ~/.cache/lme-perf/rv2/runs/*-"${LABEL}" 2>/dev/null | head -1
