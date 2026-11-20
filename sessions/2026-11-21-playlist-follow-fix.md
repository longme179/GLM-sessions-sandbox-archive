# Session 2026-11-21 (Agent-2) — playlist "Next image" palette follow: audit, fix (#181), deploy, live verify

Owner live report after PR #180: turning the follow toggle on changed the
theme immediately (fix confirmed), but pressing "Next image" in the wallpaper
playlist changed the wallpaper WITHOUT the palette following. Ask: audit
deeper, then deploy on the machine for them to try.

## 1. Audit — the exact break

- "Next image" (qml/settings/WallpaperPlaylistSettings.qml:47) runs the
  backend action `wallpaperNext`. In desktop_backend.py:593-596 the wallpaper
  capabilities were wired as:
  `apply` → host method `apply_wallpaper` (which composes
  `follow_wallpaper_palette` — the ONLY follow composition, from P1-1);
  `advance` → `self.wallpapers.advance` and `reset` →
  `self.wallpapers.reset_output` — straight to the legacy module, bypassing
  the host entirely, so the follow never fired on the playlist-advance and
  output-reset paths. The native automatic rotation was already covered
  (WallpaperState's advance hook), and manual apply was covered — matching
  exactly what the owner saw.

## 2. Fix (PR #181, merged 0f0277b)

- Two host wrappers mirroring apply_wallpaper: `advance_wallpaper(output)` and
  `reset_wallpaper_output(output)` — after the operation succeeds they follow
  with a palette regeneration for the wallpaper the operation left active
  (resolved via `wallpapers.current` + the shared `output_name` mapping,
  imported as `wallpaper_output_name`).
- Capabilities rewired through the wrappers; desktop_backend.py ceiling
  1625 → 1637 (architecture.json, twelve new nonblank).
- Local regression coverage: functional case (following off → advance leaves
  the palette untouched; following on → the action message gains the follow
  outcome), static pins for the wrapper defs + cap rewiring, size pin 1637.
- Battery on the branch: 1420 tests, 0 real failures; the single FAIL
  (test_local_qml minute clock) is a minute-boundary race ('00:50' vs
  '00:51') that passes standalone in 0.6 s — load flake, not a regression.

## 3. Deploy topology (verified live — useful for every future deploy)

- `~/.config/quickshell/lme-shell` → symlink to the repo, so the MAIN shell
  and its backend run off the repo tree; the SETTINGS app runs
  `deployment/bin/quickshell --no-duplicate -p <repo>/settings.qml
  --daemonize` and spawns its own `desktop_backend.py --settings` — THAT
  backend serves the "Next image" button (settings_only allowlist includes
  wallpaperNext). Deploy = merge + `git pull` on main + restart the affected
  instances. This fix was backend-Python only with no QML change, so the main
  shell (whose paths were already live from #180) was left untouched; only
  the settings app was restarted (kill + relaunch with WAYLAND_DISPLAY=
  wayland-1 XDG_RUNTIME_DIR=/run/user/1000 DISPLAY=:0).

## 4. Live end-to-end verification (real machine, real playlist, real matugen)

One-shot driver (scripts/live_next_verify.py — constructs the backend exactly
like `--settings` and calls handle() directly) on the pulled tree:

- prefs: wallpaperPaletteAuto=true, paletteSource=wallpaper (owner's live toggle)
- wallpaper: Pictures/Wallpaper1/wallhaven-w5m1y7.jpg → wallhaven-k81oj1.png
- accent: #84d992 → #c0c5e7
- result: `{"ok": true, "action": "wallpaperNext", "message": "Wallpaper
  updated (palette updated)"}` → **PALETTE FOLLOWED**

Then the settings app was relaunched onto the new tree (app 743506, backend
743519, "Configuration Loaded", no errors). Owner acceptance: press "Next
image" in the reopened Settings window.

## Known suite flakes (both pass standalone, load/timing class)

- test_managed_supervision quickshell-quit 4 s window (previous battery)
- test_local_qml minute clock (this battery, minute-boundary race)
