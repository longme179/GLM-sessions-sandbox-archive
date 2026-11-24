# Session Report: Startup Prewarm (Agent-2, 2026-11-24)

## Task
Pre-render/pre-cache every panel (especially the Activity Island) at shell startup so the first open is as smooth as later ones. Full audit → root cause → plan → fix → PR.

## Root causes found (lme-fedora-niri-qs @ main da5536a)
1. **Activity Island prewarm stall** — shell.qml's 6.5s startup timer mounts the island, but SlideLoader incubates async and Quickshell only advances async incubation on rendered frames. An idle scene renders none → dormant mount frozen in Loader.Loading → first real open pays the whole build. (The 4s stage timer avoids this with `asynchronous: false`; the island did not.)
2. **PanelStage built only the `control` page** — power, launchpad, launcher, overview, tray, wifi, clipboard, equalizer, notifications panels each built on first click.
3. **Control Center tab walk gated on visibility** — warm-up timer ran only while the panel was open.
4. **Settings app pages** — every unvisited page built on first click.

## Fix (PR #198, branch perf/startup-prewarm, commit 2a0634b, 5 files +61/−1)
- **SlideLoader**: idle-scene incubation pump — `FrameAnimation { running: mounted && status === Loader.Loading }` gives the async incubator its time slices; stops itself when the item lands.
- **PageHost**: `prewarm(source, gate)` — staggered background walk, one synchronous build per 350ms tick, paused while the gate reports a busy surface.
- **PanelStage**: 6s after the stage settles, walk every openable panel (legacy kinds + catalog panels).
- **ControlCenter**: tab warm-up also runs while the tree is retained in the background.
- **SettingsView**: after first page paints, walk remaining settings pages, paused while hidden.

## Verification
- Live restart with patches: config loads, zero runtime errors.
- IPC toggles of Activity Island, launchpad, power, overview: all clean, warm opens.
- `./scripts/check.sh`: all green.
- Retained-set RSS ~406 MB (RAM caps lifted by owner order in PR #197).

## Incident & lesson
First push had `(source || []).()` in PageHost.prewarm() — a QML syntax error. qmllint reported it but my grep filter hid it; the live load test caught it (`Expected token identifier` in config error log). Lesson: read full linter output; always run the real loader before committing.

## State left behind
- Host: lme-fedora-niri-qs on `main` (user's shell running, stable). Branch `perf/startup-prewarm` pushed; PR #198 open.
- To get the behavior: merge PR #198 and restart quickshell.
- qs-dms submodules (dux-qml-common, dux-qt-base) initialized for reference.
