#!/usr/bin/env bash
# Install the eyes into the repo checkout — part 1: copy eyes.py only.
set -u
R=~/.cache/lme-perf/rv2/repo/scripts/perf
T=~/.cache/lme-perf/rv2/p-head/scripts/perf
cd "$R" || exit 1
cp "$T/eyes.py" eyes.py && echo copied
ls -la eyes.py
git -C ~/.cache/lme-perf/rv2/repo log --oneline -1
