# Session 2026-11-23 (Agent-2) — wallpaper palette follow: audit, fix, PR #191

Owner report (Vietnamese): auto playlist rotation changes wallpaper but the
palette does NOT follow; "Next image" in Settings DOES. Ask: audit whole shell,
definitive fix, + a "next wallpaper" widget for topbar and CC tiles.

## Root causes (all on main @ 8027691, PR #191 fixes all three)

1. **RC1 — `--no-wallpaper` polarity inverted** in desktop_backend.py::main
   (line 1595): `no_wallpaper=not(args.once or args.no_wallpaper or ...)`.
   Main backend runs WITH the legacy Python scheduler despite ShellState.qml
   spawning it with `--no-wallpaper`; Python wins the deadline race, rotates
   via `wallpaperCycle` (no palette follow), and its pref write resets the QML
   machine signature → the native scheduler (which HAS the follow) is starved
   forever. The user's exact symptom.
2. **RC2 — WallpaperState.qml busy-wedge**: executeAdvance/executeRestore/
   wallpaperStatus/wallpaperEnsure set `busy=true` BEFORE ready()→runTool(),
   and runTool queues when busy → first scheduler job never runs, busy latches
   forever. Masked by RC1. Tests missed it because they inject `runner`
   (bypasses queue). Fix: remove the 4 premature assignments (runTool owns busy).
3. **RC3 — wallpaperCycle had no palette follow**: composed
   follow_wallpaper_palette into the scheduler job (defense in depth), same as
   apply_wallpaper/advance_wallpaper (PR #181 precedent).

## Widget delivered

- Bar module: config/wallpaper.json `bar` block + startup mirror in
  config/features.json (line-surgical patch — a global json.dump reformats the
  whole one-line-per-feature file, bloating the diff) + qml/bar/WallpaperButton.qml
  (EqualizerButton pattern). Auto-appears in Settings→Top bar→Available modules.
- CC tile: control-grid.json tile `wallpaper` (1x1 row 8 col 3, beside
  equalizer), ControlDashboard wallpaperModule + components map, desktop_features
  migrations (4 combos: wallpaper; batterySaver+wallpaper; equalizer+wallpaper;
  batterySaver+equalizer+wallpaper — equalizer commit 2b29402 precedent),
  LEGACY_GRID_IDS exclusion.
- New `image` glyph in ShellIcon (picture frame + sun + mountain).
- Ceilings ratcheted: ControlDashboard 338, desktop_backend 1652,
  control-grid.json 254, architecture.json 418 (self-referential cap!).

## Workflow traps hit this session (worth remembering)

- **tests/ is UNTRACKED in the published repo** (.gitignore "Local-only working
  set since 2026-11-13") — sandbox clones have NO tests; test additions must
  run host-side via Agent-1. PR body must say so.
- features.json line-surgery: match BOTH '"id":"wallpaper"' AND
  '"descriptor":"config/wallpaper.json"' on the same line; my first patch hit
  the weather feature (first "startup":{"settingsPage" in file) — assert the
  right line and verify the untouched neighbor afterward.
- catalog check: run with `PYTHONPATH=scripts python3 -I -c "import
  feature_catalog; feature_catalog.load_catalog()"` from repo root (check.sh
  works too; direct ./scripts/feature_catalog.py fails on module path).
- architecture.json's own ceiling is self-referential — every largeFiles edit
  needs the cap bumped in the same commit.

## PR #191 (OPEN): fix/wallpaper-palette-follow — commit 06d4a2a

Sandbox validation: py_compile, JSON validity, check-architecture.sh clean after
ratchets. Host-side pending (owner or next session via Agent-1 on
/home/kimhoanglong/Desktop/dev-lme-shell): ./scripts/check.sh, focused
test_control_grid/test_features/test_native_wallpaper, NEW regression tests
(main() polarity pin; wallpaperCycle follow functional case; WallpaperState
unwedge engine case WITHOUT injected runner + fake awww), then merge + deploy
(main shell restart needed — QML changed).

Also NOT fixed (same-class minor gap, noted in PR): gowallApply →
ImageUtilities.apply → Wallpapers.apply bypasses the host wrapper (no palette
follow on gowall-applied wallpapers).
