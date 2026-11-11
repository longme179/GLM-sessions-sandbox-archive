#!/usr/bin/env bash
# run_baseline.sh — A2: full baseline re-measurement (Minewrap memtest harness).
#
# Runs every scenario of the v1.9.3 report §13 (S0/S1/S3/SR/SW[/SW2] + GUI),
# RUNS times each (default 2), then builds results/baseline-v1.9.3.md with
# median [min–max] + tolerance verdicts against the report reference.
#
# Usage:
#   ./run_baseline.sh /path/to/minewrapd [ /path/to/minewrap-tauri ]
# Env:
#   RUNS=2  SECS=30  SR_SECS=35  SW2=1 (skip by default)  GUI_DISPLAY=xvfb|:99…
#     GUI_DISPLAY=xvfb  -> gui_scenario.py --xvfb "$DISPLAY_VAL" (headless)
#
# STANDALONE tool (policy Q8): never commit this into the Minewrap app repo.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"

DAEMON=${1:?usage: run_baseline.sh <minewrapd-release-binary> [minewrap-tauri-binary]}
GUI=${2:-}
RUNS=${RUNS:-2}
SECS=${SECS:-30}
SR_SECS=${SR_SECS:-35}
SW2=${SW2:-0}

[[ -x "$DAEMON" ]] || { echo "minewrapd not executable: $DAEMON" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 required" >&2; exit 1; }

run() { echo ">>> $*"; python3 "$@"; }

# --- daemon scenarios -------------------------------------------------------
for i in $(seq 1 "$RUNS"); do
  run scenario.py --config configs/idle0.toml --binary "$DAEMON" --label "S0#$i" --seconds "$SECS"
  run scenario.py --config configs/idle1.toml --binary "$DAEMON" --label "S1#$i" --seconds "$SECS"
  run scenario.py --config configs/idle3.toml --binary "$DAEMON" --label "S3#$i" --seconds "$SECS"
  run scenario.py --config configs/run.toml  --binary "$DAEMON" --label "SR#$i" --seconds "$SR_SECS" --start survival
  run scenario.py --config configs/run.toml  --binary "$DAEMON" --label "SW#$i" --seconds "$SR_SECS" --start survival --ws survival
  if [[ "$SW2" == "1" ]]; then
    run scenario_env.py configs/env-wt2.env -- --config configs/idle0.toml \
        --binary "$DAEMON" --label "SW2#$i" --seconds "$SECS"
  fi
done

# --- GUI scenario -----------------------------------------------------------
if [[ -n "$GUI" ]]; then
  [[ -x "$GUI" ]] || { echo "minewrap-tauri not executable: $GUI" >&2; exit 1; }
  for i in $(seq 1 "$RUNS"); do
    if [[ "${GUI_DISPLAY:-}" == "xvfb" ]]; then
      run gui_scenario.py --binary "$GUI" --label "GUI#$i" --seconds 30 --xvfb "${DISPLAY_VAL:-:99}"
    else
      run gui_scenario.py --binary "$GUI" --label "GUI#$i" --seconds 30
    fi
  done
else
  echo ">>> GUI binary not given — skipping GUI scenario (pass it as arg 2)"
fi

# --- report -----------------------------------------------------------------
run report.py --out baseline-v1.9.3.md
echo "Done. See results/baseline-v1.9.3.md"
