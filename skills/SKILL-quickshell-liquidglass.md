# SKILL: Quickshell + Liquid Glass (lme-fedora-niri-qs)

The user's shell: `github.com/longme179/lme-fedora-niri-qs` — a Quickshell/QML
desktop shell on **Fedora + Niri/Wayland**, running on their machine
(`~/.config/quickshell/lme-shell` symlinks to the repo checkout at
`~/lme-fedora-niri-qs`). Reference blueprint for the glass work:
**Serpantinum** (`github.com/ilyamiro/serpantinum`) — copy its approach
verbatim, then adapt; AGPL-3.0, keep attribution headers.

## Runtime facts (re-verify after upgrades)

- quickshell 0.3.2, niri 26.04, eDP-1 1920x1080@120, scale 1
- screenshots: `grim` (full or with `-g` crops); restart shell:
  `~/.local/bin/lme-shell start`; logs land in `log.qslog` per instance dir
- current prefs: `surfaceStyle=liquid`, `barStyle=islands`, applied backdrop
  blur preset = `true` (xray false)

## Validation battery (run for EVERY change; qmllint alone is NOT enough)

1. `qmllint` on changed QML files
2. `scripts/check-architecture.sh` — size caps live in `architecture.json`
   (ratchets: e.g. liquid-glass.frag 221, Theme.qml 250); trim comments or
   compress ternaries when a change pushes over a cap
3. `python3 scripts/feature_catalog.py --check`
4. shader touched → rebuild: `QSB_BINARY=/usr/lib64/qt6/bin/qsb bash scripts/build-shaders.sh`
5. `PYTHONPATH=scripts:tests python3 -m unittest tests.test_...` (relevant modules)
6. restart shell + `grim` visual verification; verify in EVERY mode the
   change can touch (islands AND connected bar; wallpaper AND app windows
   behind panels; light AND dark wallpapers)

## Singletons (the expensive crash)

A QML singleton MUST have `pragma Singleton`, `import Quickshell`, root
`Singleton {}`, and registration in `qml/services/qmldim`. qmllint does NOT
catch a missing `import Quickshell` — the shell crashes at startup. This
burned a whole session once (EQ singleton).

## Liquid Glass architecture (state after PR #90)

Two independent layers — understand both before touching optics:

1. **Lens optics (wallpaper-sampling shader)** — `GlassPanel` →
   `GlassMaterial` (tint/tap coords) → `GlassOptics` (ShaderEffect running
   `qml/components/shaders/liquid-glass.frag.qsb`). Backdrop = a per-output
   wallpaper snapshot Image (`GlassBackdrop.qml`; cache
   `~/.cache/lme-shell/glass/<output>.png` + `?rev=` bump, ref-counted in
   `GlassState.qml`; `scripts/glass_snapshot.py` copies the live wallpaper
   or writes a 1×1 flat tile for color wallpapers). Shader: LOD-pyramid
   `blurredAt`, rim/fresnel/fringe/grain; tint `tA=clamp(tintAmount*(0.7+0.6*l),0,1)`
   where `l` is backdrop luminance.
2. **Compositor blur (real frost of app pixels)** —
   `shell.qml` sets `BackgroundEffect.blurRegion` per window; regions from
   `BarSurface.qml` (bar) and `SurfaceBlurRegion.qml` (popups). Niri config:
   `config/niri/popup-blur.kdl` + deployed `~/.config/lme-shell/liquid-blur.kdl`;
   `xray true` = blur wallpaper only (cheap), `xray false` = blur apps+wallpaper
   (experimental, expensive, niri ≥ 26.04 only).

**The yield mechanism (PR #88/#89)**: when the true-backdrop preset is
applied (`glass.appliedBlur==="true"`, xray false) AND the surface's blur
region is active AND niri ≥ 26.04, shader uniform `compositorBlur` flips the
lens base transparent (tint cap ~0.15) so the compositor frost of APP pixels
shows through the panel — without it, panels painted the stale wallpaper
snapshot over app windows (the "panels pierce through apps" bug). Theme
gates: `compositorTrueBlur` → `compositorBarBlur` (bar pills, wired through
BarGroup/BarModule/LiquidButton) / `compositorPopupBlur` (popups).
Bar blur region = the ACTUAL glass surfaces only: islands = the 3 pills
(Never a full-strip region — that painted a continuous 1-pill band, PR #89),
connected = the visible BarSurface.

**Adaptive tint (PR #90)**: `Theme.glassAdaptiveTint(tA,l)` pure function —
bright backdrop darkens the glass for text contrast; bounded
`[0.7*tA, min(1.6*tA, 0.9)]` then `[0,1]`; pref `adaptiveContrast` default
off, battery saver forces off; in yield mode the tint cap relaxes 0.15→0.22
only while adaptive is on and luminance > 0.55.

**Material presets (PR #90)**: settings group "Material (lens)" —
Clear/Frosted/Vivid write the EXISTING slider keys (no schema change);
the OTHER group is "Backdrop blur (compositor)" (xray true/false) — two
different "Frosted" meanings, don't conflate them.

**Lens 2.0 (PR #90)**: `StretchIndicator.qml` internals — leading edge
200ms OutExpo / trailing 350ms; `liftMagnify` 1.16 while moving; `placed`
latch (fade out, no ghost rect at 0,0); 300ms settle on `Theme.liquidGlass`
toggle. NEW timing is default; opt-out via `legacyMotion=true`. Global
`motion.springMotion` is used by 13+ surfaces — never flip its default.

**Idle & a11y (PR #91)**: `GlassMaterial` has a single `dirty` gate in
`onAfterAnimating` (telemetry sample first, then `if(!dirty) return`) —
zero JS for unhovered+static; `updateLight` further gated by
hovered||hoverAmount>0. `FrameLogger` singleton, env `LME_GLASS_TELEMETRY=1`
(per-class p50/p99, 10s flush). At idle a Wayland compositor renders ZERO
frames — silent telemetry at idle is SUCCESS; idle evidence comes from
/proc CPU sampling (sudo needs a password on the machine; sysstat absent).
`reducedTransparency` pref (Accessibility) rides the same Theme gate as
battery saver (`Theme.liquidGlass = !batterySaver && !reducedTransparency &&
surfaceStyle==="liquid"`); blur gates honor it; live-swaps within one ~2s
poll cycle (Settings UI `setting` IPC → backend `preferences.set` → revision
bump → snapshot → QML reactive binding). `Theme.glassContrastFloor`
(white-text 3:1, composite ≤0.30, yield cap 0.30/normal 0.75) chains after
adaptive tint; bypass under batterySaver||reducedTransparency.
Idle CPU stays ~11.9% — attributed to Qt/driver threads, not shell QML
(follow-up issue #92). `/usr/bin/qmllint` is Qt5 1.0: exits 255 on
`pragma ComponentBehavior: Bound` files — use `./scripts/check.sh` as the
real gate. Schema goldens MUST be updated in the same PR that adds keys
(PR #90 shipped a red golden; #91 fixed it).

## Repo layout map

- `shell.qml` → `FeatureBootstrap.qml` loads panels per `config/features.json`
- `qml/components/` GlassPanel, GlassMaterial, GlassOptics, GlassBackdrop,
  SurfaceBlurRegion, StretchIndicator, LiquidButton, GlassNesting.js
- `qml/theme/Theme.qml` — glass tokens + gates (size-capped!)
- `qml/bar/` BarSurface, BarGroup, BarModule; `qml/panels/Bar.qml`
- `qml/services/` singletons + `qmldim`; `scripts/` python backends
  (glass_snapshot.py, liquid_glass.py, desktop_backend.py)
- `config/liquid-glass.json` glass controls; `config/niri/*.kdl`
