# lme-fedora-niri-qs — live state

> UPDATE THIS FILE at the end of every work session. Last updated:
> 2026-11-07 (night session — glass simplification PR #96 opened; late
> session — niri 26.04 capability snapshot: knowledge/niri.md).

## Open PR (awaiting owner review)

- **#96** `fix(glass): drop backdrop sampling - simple transparent glass
  (tint, grain, edge + compositor blur)` (branch `fix/glass-no-backdrop`,
  commits `63eb9b9` + `09f299c` + `0f3a9d9`, pushed 2026-11-07): the user
  rejected the whole hybrid model with a binding directive — "I only want
  transparent glass with simply adjustable blur/noise/grain. I do NOT want
  the glass shader to take ANY information about the desktop background.
  Don't overcomplicate things." So the wallpaper-sampling lens is now GONE:
  deleted GlassBackdrop.qml / GlassSampling.js / GlassGeometry.js /
  scripts/glass_snapshot.py + the ~/.cache/lme-shell/glass snapshot cache;
  liquid-glass.frag rewritten to 95 nonblank lines with NO sampler2D — one
  tint path `A = clamp(B + panelOpacity*0.75, 0, 0.92)`,
  `B = clamp(tintAmount*0.85, 0, 0.15)`, plus grain + geometry edge/rim;
  yield/compositorBlur/adaptiveContrast/yieldOpacity uniforms all dead.
  Removed Theme adaptive/contrast-floor helpers + compositor*Blur gates,
  "True backdrop (experimental)" combo, "Adaptive contrast" switch,
  "Lens blur" slider, frosted/true presets; liquid_glass.py snippet() is
  always `xray false` (niri >= 26.04 gate kept), validate drops retired
  inner keys blur/blurPreset/appliedBlur so old settings.json survives.
  Settings card now: presets (surviving keys only) / tint picker /
  opacity+rim+edgeWidth+grain sliders / Glass selection switch /
  Compositor blur group (status + passes + spread + Save snippet).
  check.sh: 1064 tests, 1 failure = the known #94 stale 149-schema guard
  (150 != 149 here, 151 != 149 on main — same #94 root). Blur regions
  (bar pills, popups) untouched — niri is now the ONLY blur. Live-verified:
  shell restarted on the branch, cache dir not recreated, over a spawned
  magenta kitty the Settings glass showed blurred WINDOW content (never
  wallpaper), settings.json backup/restore byte-exact around the opacity-0
  test. Bar pills show blurred wallpaper sky behind them — CORRECT: the
  bar reserves exclusive zone so windows don't extend under it (pixel-hue
  analysis proved the magenta window starts below the bar).
  **The live checkout is ON this branch; the user is running it.**
  User's live liquidGlass: tint #b5465668, **opacity 0.0** (they left it at
  0 from testing #95 — tell them to raise Panel tint opacity back up).

## Merged through PR #95 (`7a11fc6`)

- #95 `fix(glass): let Panel tint opacity govern the compositor-yield tint`
  (yieldOpacity uniform, alpha ceiling 0.92) — treated the x-ray symptom
  at parameter level; correlation 0.55→0.05 at the user's opacity 1.0, but
  the user still saw the background at opacity 0 and rejected the hybrid
  model outright → superseded architecturally by PR #96 (full backdrop
  removal). Lesson: when a visual bug survives a parameter fix, check
  whether the architecture itself contradicts the user's mental model.

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

## Runtime facts (2026-11-07 night, on branch fix/glass-no-backdrop / PR #96)

- Fedora + Niri 26.04 (rpm installed 2026-10-30), quickshell 0.3.2 (deployed
  runtime `~/.local/share/lme-shell/deployment/bin/quickshell` → symlink to
  `/usr/bin/quickshell`), eDP-1 1920x1080 scale 1; no systemd units — niri
  `spawn-at-startup` runs `~/.local/bin/lme-shell start` (logs land in
  `~/.local/state/lme-shell/log/lme-shell.log`, rotated at 1 MB)
- surfaceStyle=liquid, barStyle=islands; liquidGlass after #96: tint
  `#b5465668`, **opacity 0.0** (user left it low while testing), rim 2.0,
  edgeWidth 0.25, grain 0.08, passes 2, offset 3; retired keys blur/
  blurPreset/appliedBlur dropped on load; wallpaper STATIC
  (`Pictures/Wallpaper1/wallhaven-w5m1y7.jpg`, playlist disabled by the
  user for this debugging session); `~/.cache/lme-shell/glass/` deleted,
  not recreated
- niri config includes: `lme-shell-deploy.kdl` then
  `~/.config/lme-shell/liquid-blur.kdl` (xray false, blur passes 2 offset
  3); deploy.kdl additionally carries a USER-ADDED unscoped window-rule
  (`geometry-corner-radius 28; clip-to-geometry true; background-effect
  { blur true }` — applies to ALL windows; not from the repo, leave it)
- live checkout on branch `fix/glass-no-backdrop` (PR #96, NOT merged) —
  after merge: `git switch main` + restart shell
- qsb tool: `/usr/lib64/qt6/bin/qsb` (qt6-qtshadertools 6.11.2)
- bar reserves exclusive zone: app windows start BELOW the bar strip — the
  wallpaper sky is genuinely what is behind the bar pills (pixel-hue
  analysis, 2026-11-07 night; matters when interpreting screenshots)
- niri 26.04 IS the latest stable (2026-04-25; repo moved to the niri-wm
  org). Full capability snapshot + layer-rule/blur reference:
  knowledge/niri.md. main = 26.04 + 264 unreleased commits (max-bpc, stylus
  binds, …) — do not design against them

## User-side checks still pending (tell the user, don't assume)

- **#96 (THE one that matters now)**: the user is running the branch live.
  Eyeball Settings → Night Light over the desktop AND over a browser
  window: the shell no longer paints ANY wallpaper — what shows through
  the glass is only niri's blur of what is really behind. Raise **Panel
  tint opacity back up (their live value is 0.0 from testing!)** — 0 =
  clear glass, 0.65 default, 1 ≈ frosted 0.9 tint. If the background is
  still too recognizable at their preferred tint: raise **Blur passes /
  Blur spread** in the Compositor blur group and hit **Save niri blur
  snippet**. Merge PR #96 when happy, then `git switch main` + restart.
- **niri caveat when judging #96** (26.04 docs — knowledge/niri.md §2):
  non-xray blur (`xray false`, our mode) is upstream-EXPERIMENTAL — it
  disappears during window open/close animations and while dragging a
  tiled window. A flash of un-blurred glass in those moments is niri's
  known limitation, NOT a shell bug. For stronger cheap blur: raise Blur
  spread (offset) before Blur passes.
- #77: visual live-swap of reduced-transparency on their real screen;
  hover/glint feel (ydotool missing on the machine)
- EQ real-machine check (band drag, Apply, presets, Dynamic EQ, Audio view)

## Update protocol

When a PR merges: append a one-liner above, move open-work items, refresh
runtime facts, list any new pending user-side checks, then commit+push this
archive (via desktop, see SKILL-github-pr-workflow.md).
