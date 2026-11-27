#!/usr/bin/env bash
# p-main probe-tree touch-up: its export predates the settingsHover fix (the probe
# reads watched.point, but SettingsView registered itself - an Item without .point).
# One-line fix, same as the tree already carries on p-head.
set -u
F=~/.cache/lme-perf/rv2/p-main/qml/settings/SettingsView.qml
grep -n "settingsHover = this" "$F" || { echo "anchor missing"; exit 1; }
sed -i 's/Probe.settingsHover = this;/Probe.settingsHover = pointerWatch;/' "$F"
grep -n "settingsHover = " "$F"
# parse check with the harness's own preflight against this tree
cd ~/.cache/lme-perf/rv2/repo/scripts/perf || exit 1
export WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/1000
python3 - <<'PY' || exit 2
import subprocess, os
QS = os.path.expanduser("~/.local/share/lme-shell/deployment/bin/quickshell")
env = {**os.environ, "LME_PERF_TREE": os.path.expanduser("~/.cache/lme-perf/rv2/p-main")}
r = subprocess.run([QS, "-p", "preflight.qml"], env=env, capture_output=True, text=True, timeout=60)
print(r.stdout[-400:], r.stderr[-200:])
PY
