# lme-fedora-niri-qs — live state

> UPDATE THIS FILE at the end of every work session. Last updated:
> 2026-11-07 (after PR #93 merge — Liquid Glass 2.0 epic COMPLETE).

## Merged through PR #93 (`bde3c47`)

Recent history (newest first):

- #93 `feat(glass): settings presets + Lens/Compositor grouping, GLASS.md,
  attribution (#78)` — closes #78 AND epic #72 (explicit "Closes #72" needed:
  no GH sub-issue linkage was ever recorded; all sub-issues #73–#78 now
  closed). `LiquidGlassSettings.qml` restructured: preset row (Clear/Frosted/
  Vivid + one-line descriptions via `glassMaterialPresetDesc`) moved to top of
  material card; sliders regrouped `glassLensHeader` (blur/rim/edgeWidth/
  grain/opacity) + `glassCompositorHeader` (passes/offset, compositor-wide copy
  on the header); new `glassBlurStatus` derived status line: applied(<preset>) /
  pending (save snippet) / unsupported (niri < 26.04, detected <version>). All
  objectNames preserved; NO new pref keys (schema goldens untouched); arch cap
  entry added for tests/test_glass_controls.py (264). New `docs/GLASS.md`
  (hybrid model, per-control table with real defaults/ranges, Frosted vs True
  tradeoff, measured idle facts from #77, 6-scenario p50/p99 marked NOT
  measured, troubleshooting) linked from CONFIGURATION/TROUBLESHOOTING/README
  Features+Documentation. Serpantinum-NOTICE + THIRD_PARTY.md extended with
  #87–#91 renderer refinements (yield/adaptive/grain/floor) + explicit Lens 2.0
  timing derivation (StretchIndicator ← GlassLens@87d3b927, no engine copied,
  MIT SPDX kept). feather/smearing/brightness documented as not-shipped (issue
  text listed controls that never existed). Pre-existing main failures filed as
  follow-up **#94** (stale 149 schema guard, selection-lens source drift,
  settings-startup reconnect, pixel-test sensitivity; qmllint 255 = lesson 19).
  Post-merge: shell restarted on main — MUST be setsid-detached (lesson 23);
  bar recovery verified via top-strip pixel diff vs dead-state screenshot.

- #91 `feat(glass): idle-frame elimination, frame telemetry, reduced
  transparency, contrast floor` — GlassMaterial `dirty` gate (zero JS for
  unhovered+static; telemetry samples before the gate); FrameLogger singleton
  env-gated `LME_GLASS_TELEMETRY` (per-class p50/p99, 10s flush);
  `reducedTransparency` pref (Accessibility; same Theme gate as battery saver
  incl. blur gates; verified live-swap within one ~2s poll cycle, no restart);
  `Theme.glassContrastFloor(alpha,l,tintLum)` white-text 3:1 clamp
  (composite ≤0.30; yield cap 0.30 / normal 0.75; chained after adaptive tint;
  bypass under batterySaver||reducedTransparency). Schema golden updated in the
  same PR (151 keys incl. reducedTransparency/adaptiveContrast/grain 0.004).
  Idle CPU before/after indistinguishable ~11.9% (zero frames at idle by
  design — Wayland skips rendering); per-thread table shows the cost is
  Qt/driver internals (QSGRenderThread/WaylandEventThr/GPU helpers) + main
  4.13% — follow-up issue #92 filed with the table. Measurement tables posted
  on issue #77 (issuecomment-6699165710).

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

- **#94** (follow-up): stale test guards + env-sensitive failures on main
  (149→151 schema guard, selection-lens source assertion, settings-startup
  reconnect, pixel tests, qmllint-255 note)
- **#92** (follow-up, no milestone): profile & reduce ~11-12% quickshell idle
  CPU with zero rendered frames (per-thread table in the issue; perf/QML
  profiler attribution needed)

## Runtime facts (2026-11-07)

- Fedora + Niri 26.04, quickshell 0.3.2, eDP-1 1920x1080@120 scale 1
- surfaceStyle=liquid, barStyle=islands, applied backdrop blur=true (xray false)
- wallpaper: `Pictures/Wallpaper1/...`; snapshot cache live per output

## User-side checks still pending (tell the user, don't assume)

- #78/#93: open Settings → Appearance → Liquid glass material and eyeball the
  new layout (presets at top with descriptions, Lens/Compositor sub-headers,
  status line); try preset switching + a compositor blur save to see
  pending→applied (no pointer automation on the machine — QML test covered it,
  human eyes did not)
- #77: visual live-swap of reduced-transparency on their real screen (chain
  verified + screenshots captured; model cannot read pixels); contrast
  readability on their own wallpapers (brightest available was ~gray 111/255,
  not near-white); hover/jelly lens feel (ydotool missing on the machine)
- #76 leftovers: lens motion feel on live tab bars, preset cycling, battery
  saver glass-off
- EQ real-machine check (band drag, Apply, presets, Dynamic EQ, Audio view)

## Update protocol

When a PR merges: append a one-liner above, move open-work items, refresh
runtime facts, list any new pending user-side checks, then commit+push this
archive (via desktop, see SKILL-github-pr-workflow.md).
