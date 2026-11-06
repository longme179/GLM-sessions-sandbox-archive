# lme-fedora-niri-qs — live state

> UPDATE THIS FILE at the end of every work session. Last updated:
> 2026-11-07 (after PR #90 merge).

## Merged through PR #90 (`6b2e076`)

Recent history (newest first):

- #90 `feat(glass): lens 2.0 + adaptive tint + material presets + tunable grain`
  — StretchIndicator 200/350ms OutExpo, lift+magnify 1.16, placed latch, 300ms
  settle; `legacyMotion` opt-out (new timing is default; global springMotion
  untouched). `Theme.glassAdaptiveTint` bounded [0.7tA, min(1.6tA,0.9)],
  `adaptiveContrast` pref (default off, battery saver forces off), yield cap
  0.15→0.22 while adaptive+l>0.55. Material presets Clear/Frosted/Vivid in
  "Material (lens)" group; blur group relabeled "Backdrop blur (compositor)".
  Grain slider 0–0.08 default 0.004 (= old hard-coded value).
- #89 `fix(glass): islands bar blur follows pill shapes` — removed PR #88's
  fullStrip region (it painted a continuous 1-pill band in islands mode);
  bar pills now yield with the bar flag (BarGroup/BarModule/LiquidButton
  wiring); popups keep the popup flag.
- #88 `fix(glass): yield lens to compositor blur over apps + full-strip bar
  blur region` — shader uniform `compositorBlur`: transparent base (tint cap
  0.15) so compositor frost of app pixels shows through panels; fixed the
  "panels show stale wallpaper over app windows" bug. (fullStrip part later
  reverted by #89.)
- #87 blur strategy presets (xray true/false, hairline border, version gate)
- #80/#81 backdrop snapshot cache (`~/.cache/lme-shell/glass/<output>.png`,
  rev bump, flat tile for color wallpapers)
- #79 glass-on-glass nesting (GlassNesting.js ancestor walk, AGPL Serpantinum)
- #71 EQ rework after Serpantinum (band stagger etc.); #64–#68 audit fixes
  (see CHANGELOG.md in the repo for the full list)

## Open work (Liquid Glass roadmap)

- **#77** (next): idle CPU=0 / telemetry / reduced-transparency support
- **#78**: Settings UX + `docs/GLASS.md` + AGPL compliance pass

## Runtime facts (2026-11-07)

- Fedora + Niri 26.04, quickshell 0.3.2, eDP-1 1920x1080@120 scale 1
- surfaceStyle=liquid, barStyle=islands, applied backdrop blur=true (xray false)
- wallpaper: `Pictures/Wallpaper1/...`; snapshot cache live per output

## User-side checks still pending (tell the user, don't assume)

- Lens motion feel on live tab bars / settings sidebar (lens 2.0)
- Material preset cycling + grain extremes in Settings UI
- Battery saver → glass off
- EQ real-machine check (band drag, Apply, presets, Dynamic EQ, Audio view)

## Update protocol

When a PR merges: append a one-liner above, move open-work items, refresh
runtime facts, list any new pending user-side checks, then commit+push this
archive (via desktop, see SKILL-github-pr-workflow.md).
