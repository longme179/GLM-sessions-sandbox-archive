# lme-fedora-niri-qs — live state

> UPDATE THIS FILE at the end of every work session. Last updated:
> 2026-11-07 (evening session — glass "xray" complaint, PR #95 opened).

## Open PR (awaiting owner review)

- **#95** `fix(glass): True backdrop glass reveals the desktop background —
  scale yield tint with Panel tint opacity` (branch
  `fix/glass-xray-wallpaper-leak`, commits `c46fe30` + `11601d3`, opened
  2026-11-07): root cause = `liquid-glass.frag` yield branch hard-capped its
  tint at alpha 0.15/0.22 (output 0.85), so with the True backdrop preset
  the glass stayed ~85% see-through and the blurred desktop wallpaper
  remained recognizable through panels/bar/Settings (user: "render như kiểu
  xray"). The Panel tint opacity preference was ignored in that path.
  Fix: new `yieldOpacity` uniform fed from `Theme.panelOpacity`
  (GlassMaterial → GlassOptics → frag), added into the capped yield tint,
  alpha ceiling 0.92; `.frag` kept at exactly 221 nonblank lines
  (architecture ratchet, net-zero patch); `.qsb` rebuilt with
  `/usr/lib64/qt6/bin/qsb --glsl "100 es,120,150" --hlsl 50 --msl 12`.
  Live-verified on the machine: Settings-over-desktop wallpaper correlation
  0.548/0.580 → 0.046/0.055, greenish fraction 51%→15%/2.4%; over browser
  corr ≈ 0; bar strip 0.912→0.793 (residual = raw wallpaper in the gaps
  BETWEEN islands pills — no glass there by design). Glass unit tests 41 OK
  (9 skipped); `check.sh` single failure = the known stale 149-schema guard
  already tracked as **#94** (verified failing identically on `main`).
  **NOTE: the live checkout is ON this branch right now (the user is
  running the fix); `git switch main` after merge.**

## Merged through PR #93 (`bde3c47`)

Recent history (newest first):

- #93 `feat(glass): settings presets + Lens/Compositor grouping, GLASS.md,
  attribution (#78)` — Settings → Appearance → Liquid glass material: preset chooser
  (Clear/Frosted/Vivid) moved to top; sliders regrouped Lens
  (blur/rim/edgeWidth/grain/opacity) vs Compositor (passes/offset, compositor
  wide); derived status line applied(preset) / pending (save snippet) /
  unsupported (n<iri < 26.04>, detected <ver>). No new pref keys; schema
  goldens untouched. `docs/GLASS.md` added +(hybrid model, per-control table,
  Frosted vs True tradeoff, measured idle facts from #77, 6-scenario p50/p99
  marked NOT measured, troubleshooting)* and linked from CONFIGURATION/
  TROUBLESHOOTING/README. Serpantinum/NOTICE + THIRD_PARTY extended with
  #87–91 renderer refinements + explicit Lens 2.0 timing derivation (no
  engine copied, MIT SPDX kept). Closes epic #72 explicitly (GH sub-issue
  linkage was never recorded; all #73–#78 closed). Pre-existing main failures
  filed as follow-up **#94**.
- #91 `feat(glass): idle-frame elimination, frame telemetry, reduced
  transparency, contrast floor` — dirty-gated GlassMaterial, p50/p99 FrameLogger
  (`LME_GLASS_TELEMETRY=1`), `reducedTransparency` pref (live-swap, no restart),
  automatic tint contrast floor; schema golden updated same PR; follow-up #92
  (idle CPU residual)
- #90 `feat(glass): lens 2.0 + adaptive tint + material presets + tunable grain`
- #89 fix(islands bar blur follows pill shapes)
- #88 fix(yield lens to compositor over apps + bar full-strip blur region)
- #87 backdrop blur presets +compositor yield gating, #79, #80/#71 EQ etc.

## Open work (Liquid Glass roadmap)

- **#94** follow-up: stale test guards + env-sensitive failures on main
  (9 failures from #91; qullint-255 on arch = tool mismatch, see lesson 19)
- **#92** follow-up: profile & reduce ~11-12% quickshell idle CPU with zero
  rendered frames

## Runtime facts (2026-11-07 evening)

- Fedora + Niri 26.04, quickshell 0.3.2 (deployed binary symlinks to
  `/usr/bin/quickshell`), eDP-1 1920x1080 scale 1. No systemd shell units;
  niri spawns `~/.local/bin/lme-shell start`. Logs
  `~/.local/state/lme-shell/log/lme-shell.log` (rotated @1MB).
- surfaceStyle=liquid, barStyle=islands, backdrop blur preset applied=true
  (xray false), liquidGlass tint `#70465668`, opacity 1.0, blur 2.0, rim 2.0,
  edgeWidth 0.25, grain 0.08, adaptiveContrast on; wallpaper
  `Pictures/Wallpaper1/wallhaven-w5m1y7.jpg` (playlist disabled).
- niri config includes: `lme-shell-deploy.kdl` then
  `~/.config/lme-shell/liquid-blur.kdl` (xray false, passes 2 offset 3).
  `deploy.kdl` also carries a USER-ADD unscoped window-rule applying
  `geometry-corner-radius 28 + clip-to-geometry + background-effect blur`
  to ALL windows (leave it).
- live checkout ON `fix/glass-xray-wallpaper-leak` (PR #95, open) — switch to
  `main` after merge. `qsb` at `/usr/lib64/qt6/bin/qsb` (qt6-qtshadertools 6.11.2).

## User-side checks still pending

- **#95** eyeball Settings → Night Light over bare desktop AND over a browser: wallpaper
  must no longer read through the frosted glass (tune Panel tint opacity; 65% default);
  bar gaps between islands pills still show raw wallpaper by design.
- **#78** SOURCES-FIXED: eyeball Settings → Appearance → Liquid glass material
  (presets at top, Lens/Compositor sub-headers, status line); try a preset
  switch + a compositor blur save to see pending→applied.
- #77 visual live-swap of reduced transparency > contrast readability; hover/jelly feel
- #76 leftovers (lens motion on live tab bars, preset cycling, battery saver)
- EQ real-machine check
