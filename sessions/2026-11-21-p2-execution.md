# Session 2026-11-21 (Agent-2) — P2 selective expansion: transitions (#182), lock guard (#183), widgets (#184), settings hot-reload (#185)

Owner order (P2 table): three work items with acceptance criteria —
wallpaper transition effects (3-5 curated, on awww, FPS/RAM in budget),
desktop widget enrichment (weather/calendar/user card on the canvas,
empty-region placement, drag/resize/click-through preserved), two-way
config hot-reload (schema-as-defaults JsonAdapter spirit: external file →
UI within 1 s, UI → file, debounce, automated write-read-write loop).
i18n deferred by the owner ("tạm thời, ta sẽ chưa làm Khung i18n").

## Recon findings that shaped the work

- **Transitions already existed end to end** — TRANSITIONS (12 types),
  wallpaperTransition* prefs, image_arguments → awww flags, QML mirror in
  WallpaperModel.js, validation incl. duration 0.1–10 s. Missing: the
  Settings card never offered the effect or the duration (only
  fps/step/angle/position/bezier/wave/resize/filter).
- **Widget machinery is type-agnostic** — DesktopWidgetWindow/DesktopCard
  never read `type` except for the card body; the validator's tuple was the
  only backend gate. add() used a fixed cascade, not empty-region logic.
  WeatherWidget.qml existed (bar/dashboard) but the architecture graph
  forbids DesktopCard → WeatherWidget (cross-layer panel consumption).
- **Hot-reload was half-built** — snapshot() already calls
  preferences.reload() on every publish, so external edits landed within
  the ~2 s poll; nothing woke the loop earlier, and no watcher existed.
  Preferences._write is atomic and refreshes its own stamp; QML controls
  publish on release (event-level debounce).

## PRs (stacked: #182 ← #183 ← #184 ← #185)

- **#182 feat/transition-effect-picker** — AwwwSettings grows the curated
  effect picker (fade/grow/outer/wipe/wave + none; any other stored awww
  type appended so presets stay honestly displayed) and a duration slider
  (0.5–8 s, 0.25 steps) via a step/prec extension of the generic slider
  row. Backend untouched; 52→59 nonblank (uncapped file).
- **#183 fix/lock-wayland-env-guard** — found by the #182 battery:
  Quickshell.env() returns null for unset variables and LockState.qml:29
  dereferenced it (`Quickshell.env("WAYLAND_DISPLAY").length`), throwing a
  TypeError in every environment that blanks the variable — the exact
  condition the adjacent comment documents. Deterministic once the gateway
  session env lost WAYLAND_DISPLAY (earlier batteries passed only because
  the variable happened to be set). One-line `(... || "")` guard + a local
  pin scanning the whole shell for other unguarded env dereferences
  (none). test_liquid_style was 3/3 red before, green after.
- **#184 feat/desktop-widget-types** — validator tuple grows
  weather/calendar/user; toolbar offers all six; DesktopState.place()
  scans a coarse grid over the target screen and skips candidates
  overlapping any widget already shown there (matches()), cascade as
  fallback; DesktopCard gets a calendar (pure QML month grid, locale
  weekday headers via Qt.formatDateTime, in-memory month navigation, today
  highlighted), an account card (USER env, initials avatar) and — after
  the battery's architecture gate rejected the WeatherWidget reuse — an
  inline compact weather card reading ShellState.weather (service-level
  dependency, layering intent preserved). Local suite: validation
  round-trips, static pins, and an offscreen engine case loading all three
  cards (~1 s).
- **#185 feat/prefs-hot-reload** — new scripts/prefs_watcher.py
  (sharedFiles; daemon thread stat-poll 0.25 s + values-object identity to
  stay silent on own atomic writes) pokes a self-pipe registered in the
  serve loop's selector; external edits now republish a snapshot well
  under a second. desktop_backend 1637→1649; architecture.json self-cap
  413→414. Local suite: unit (external edit wakes ≤1 s, own write silent)
  + a real `desktop_backend.py --settings` subprocess over the JSON-lines
  stdio protocol: UI write lands in the file, external edit republished
  <1 s (asserted), further UI write closes the write-read-write loop.

## P2.1 live acceptance measurement (real machine, one-shot backend)

env WAYLAND_DISPLAY=wayland-1 (the channel env had lost it — see #183):
user prefs transition=random/3.0 s/60 fps (random!), temporarily set to
grow/3.0/60, restored after. Real wallpaperNext apply:

- action ok, "Wallpaper updated (palette updated)", submit 0.21 s
- transition busy window 2.91 s vs configured 3.00 s (no frame starvation)
- awww RSS 26.6 → 34.7 MB (+8.1 MB transient); 0.28 core-seconds ≈ 10% of
  one core over the window
- shell RSS flat (~304 MB); aggregate 363.1 → 363.5 MiB vs the 400 MiB
  budget → WITHIN BUDGET. (FPS: the daemon renders at the configured
  60 fps; completion-within-duration is the no-starvation proof available
  without compositor instrumentation — stated as such.)

## Batteries

- #182 tip: 2 fails → 1 load flake (settings reconnect, passes standalone)
  + the real LockState null bug (#183). Guard-branch tip: fully green.
- #184 first tip: architecture gate FAIL (DesktopCard → WeatherWidget
  forbidden) — repaired inline, second tip fully green.
- #185 tip (stacks all four): first run failed ONLY on the #181-era local
  size pin (1637 vs the legitimate 1649); after refreshing the pin, the
  rerun is fully green — 1,425 tests, 0 failures (185 skips incl. the
  private-Wayland engine cases). All four PRs gated by that run.

## Process notes

- Lesson 85 (lessons-learned.md): gate-reading discipline (verdict via exit
  code, never tail -1), new-script classification mechanics (sharedFiles +
  the self-referential architecture.json cap), and the Quickshell.env() null
  trap.
- The desktop working tree carries an unexplained local modification
  (config/niri/lme-shell.kdl, flameshot window-rule removed, mtime
  13:47 +0700) — not from these patches (tests only read that file);
  left untouched and uncommitted for the owner/agent-1.
- The opencode channel env lost WAYLAND_DISPLAY today (gateway restart?);
  the transition measurement needed it explicitly. Battery engine tests
  now run with the variable unset — which is what exposed #183.
