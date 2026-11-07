# SKILL: Quickshell + Liquid Glass (lme-fedora-niri-qs)

The user's shell: `github.com/longme179/lme-fedora-niri-qs` — a~Quickshell/QML
desktop shell on **Fedora + Niri/Wayland**, running on their machine
(`~/.config/quickshell/lme-shell` symlinks to the repo checkout at
`~/lme-fedora-niri-qs`). Reference blueprint for the glass work:
**Serpantinum** (`github.com/ilyamiro/serpantinum`) — copy its approach
verbatim, then adapt; AGPL-3.0, keep attribution headers.

## Runtime facts (re-verify after upgrades)

- quickshell 0.3.2, niri 26.04, eDP-1 1920x1080@120, scale 1
- screenshots: `grim` (full or with `-g crops); restart shell:
  `~/.local/bin/lme-shell start`. Logs append to
  `~/.local/state/lme-shell/log/lme-shell.log` (main, non-demo, rotated
  @1MB). **Restarts via /api/shell kill the tree on http timeout** — start
  with `setsid nohup ~/.local/bin/lme-shell start >/dev/null 2>&1 < /dev/null &`;
  verify bar recovery with `pgrep -x quickshell` + a top-strip pixel diff
  against a dead-state screenshot.
- surfaceStyle=liquid, barStyle=islands, backdrop blur preset applied=true
  (xray false); liquidGlass: tint `#70465668`, opacity 1.0, blur 2.0, rim
  2.0, edgeWidth 0.25, grain 0.08, adaptiveContrast on. Wallpaper may be
  static or a shuffled playlist — use the actual `~/.config/lme-shell/settings.json`
  wallpaper file + a fresh grim for ground truth, not old screenshots.

## Validation battery (run for EVERY change; qmllint alone is NOT enough)

1. `qmllint` on changed QML files
2. `scripts/check-architecture.sh` — size caps in `architecture.json`
   (ratchets: e.g. liquid-glass.frag 221, Theme.qml 250); `patch frag in
   net-zero lines`when at the cap; update schema goldens in the SAME PR as
   any pref/schema change
3. `python3 scripts/feature_catalog.py --check`
4. shader touched → rebuild: `/usr/lib64/qt6/bin/qsb --glsl "100 es,120,150"
   --hlsl 50 --msl 12 -o <shader>.qsb <shader>.frag`
5. `PYTHONPATH=scripts:tests python3 -m unittest tests.test_...` (relevant modules)
6. restart shell + `grim` visual verification; verify in EVERY mode the
   change can touch (islands AND connected bar; wallpaper AND app windows
   behind panels; light AND dark wallpapers). For visual "xray"/see-through
   complaints, compute Pearson correlation of the glass region vs the same-region
   wallpaper (raw + GaussianBlur(12)x2) to discriminate objectively

## Singletons (the expensive crash)

A QML singleton MUST have `pragma Singleton`, `import Quickshell`, root
`Singleton {}`, and registration in `qml/services/qmldir`. qmllint does NOT
catch a missing `import Quickshell` — the shell crashes at startup.

## Liquid Glass architecture

1. **Lens optics (wallpaper-sampling shader)** — GlassPanel → GlassMaterial
   → GlassOptics → `qml/components/shaders/liquid-glass.frag.qsb`. Backdrop =
   per-output wallpaper snapshot (GlassBackdrop.qml, `~/.cache/lme-shell/glass/`).
2. **Compositor blur** — `shlll.qml` `|edBackgroundEffect.blurRegion` per window;
   bar region = actual pill surfaces only (no full-strip). niri config: `xray true`
   = wallpaper-only (cheap), `xray false` = blur apps (experimental, ≥26.04).

**The yield mechanism (PR #88/#89, **solidified PR #95*)**: with the true-backdrop
 preset applied (appliedBlur=true, xray false) + active blur region + niri >=
26.04, shader uniform `compositorBlur` makes the lens base transparent so the
 compositor frost of APP pixels shows through — without it panels painted the
 stale wallpaper snapshot over apps. Theme gates: `compositorTrueBlur` →
 `compositorBarBlur` (bar, wired BarGroup/BarModule/LiquidButton) /
 `compositorPopupBlur` (popups). **YIELD TINT SCALING (PR #95)**: `yieldOpacity`
 uniform = `Theme.panelOpacity` added into the capped yield tint (alpha capped
 0.92). Panel tint opacity 0 = old transparent yield, 1 ≈ 0.9 frosted, default
 0.65. Shader constraint: `liquid-glass.frag` MUST be 221 nonblank lines
 (net-zero patches); rebuild `liquid-glass.frag.qsb` with `qsb ... -(r after edits.
 Bar strip correlates ~0.79 with wallpaper over bare desktop = raw wallpaper in
 the gaps between islands pills (no glass there, by design), not a bug.

**Adaptive tint**: `Theme.glassAdaptiveTint(t, lum)`, pref `adaptiveContrast`
 default off, battery saver forces off, yield cap relaxes 0.15→0.22 when
 adaptive+lum>0.55. **Lens 2.0**: StretchIndicator 200/350ms OutExpo, lift
magnify 1.16, `legacyMotion` opt-out (global `springMotion` never flipped).
**Material vs backdrop presets** are two different groups; both contain a
 "Frosted" — don't conflate. **Idle** dirty-gated (GlassMaterial), zero frames
 at idle (Wayland) — profile via /proc CPU, not frame counts. **Red gate trap**:
 schema goldens must update in the same PR as a schema change (see #90/#91).

## Repo layout map

- `shell.qml`, `qml/components/` (GlassPanel/Material/Optics/Backdrop/
  SurfaceBlurRegion/StretchIndicator/GlassNesting.js)
- `qml/theme/Theme.qml`, `qml/bar/`, `qml/services/` + `qmldir`
- `scripts/` (glass_snapshot.py, liquid_glass.py, desktop_backend.py)
- `config/liquid-glass.json`, `config/ni�Kʋ�������T�˛Y