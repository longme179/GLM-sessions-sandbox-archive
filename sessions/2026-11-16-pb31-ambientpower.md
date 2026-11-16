# Session 2026-11-16 (part 3) — PB-31 implemented: AmbientPower

Owner picked PB-31 from report 07 and asked agent-2 to plan, code, and orchestrate
agent-1 on the implementation. Executed T05 (recon) → design → T06 (implement) →
T07 (threshold fix) despite a mid-turn sandbox recycle (see the incident note).

## Result
- Branch `feat/pb-31-ambient-power`, commit **5e8e616** (+74/−4, 5 files), worktree
  `~/lme-pb31` on the owner's machine, NOT pushed (owner merges; steps in report 09).
- NEW qml/services/AmbientPower.qml: `ambientActive = !batterySaverActive &&
  !outputCovered && !ambientSuppressed`; covered = window layout ≥98% of any screen
  (both dims), derived reactively from NiriState.section (zero timers/polling).
- 4 gate points: DesktopAmbient model (unmounts per-screen windows), MediaAmbient
  animating, AudioVisualizer spectrumEnabled + wanted (releases shared cava via the
  existing VisualizerState refcount).

## Durable knowledge
- LME already HAS a `qml/services/PowerState.qml` (battery/AC/UPower; used by
  ShellState:181) — the name is taken; ambient logic must not merge into it
  (PowerState↔ShellState cycle). E9's inventory missed this file — noteworthy.
- niri 26.04: no is_fullscreen anywhere (windows/focused/event-stream). windows[]
  layout.window_size is a [w,h] ARRAY. Outputs JSON is an object keyed by name.
- Quickshell 0.3.2 build here: ShellScreen has width/height, NO logicalWidth/Height.
- 1080p+bar geometry: normal maximized tiled window = 98.3%×93.5% (1888×1010);
  true fullscreen = 100% ⇒ threshold 0.98 separates them; 0.92 froze ambient in
  daily use (caught by the S6 headless cross-check — always cross-check thresholds
  against live data before shipping).
- LME gates in a worktree: check.sh works; full run-gates G0,G1 does NOT
  (tests/migration_checks.py is local-only; G1 wants a compositor). start.sh
  execs the live config name — no worktree preview without touching live config.
- Full implementation record: reports/inir-vs-lme/09-pb31-implementation.md
  (machine) + backup in the sandbox download/inir-vs-lme/.
