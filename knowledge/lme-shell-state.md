# lme-fedora-niri-qs — live state

> UPDATE THIS FILE at the end of every work session. Last updated:
> 2026-11-09 (documentation pass on branch `docs/annotate-and-map` — 12
> local commits, NOT pushed, awaiting owner review; PR #110 MERGED, main @
> 6c1dc3c; ran through the OpenCode desktop agent with gateway creds
> re-supplied by the owner).

## Session 2026-11-09: codebase annotation + WORKSPACE_MAP (branch local, unpushed)

Owner-authorized documentation-only pass, driven phase-by-phase via OpenCode
(methodology + traps: `skills/SKILL-codebase-annotate-map/SKILL.md`).

- **Branch `docs/annotate-and-map`** from main @ 6c1dc3c: 11 comment commits
  + 1 docs commit (`53e2c15`). 445 files, +1515/−312. NOT pushed — owner
  reviews and decides (per repo rule: no unauthorized push to main).
- **Deliverables**: `docs/WORKSPACE_MAP.md` (246 lines, 11 sections, 105
  [verified]/14 [inferred], 2 mermaid diagrams, 6 flows with file:line);
  AGENTS.md got a 4-line pointer to the map; 108 REL / 26 INVARIANT /
  10 GOTCHA tags greppable via `grep -rn "REL:"`.
- **Zero-behavior proof**: ast.dump-minus-docstrings 276/276 identical;
  string-aware comment-strip 167/167 identical; check.sh unittest `Ran 1073
  OK (skipped=185)` matching baseline; G0 completed 888 passed/0 failed.
- **Environmental flake recorded (map Finding)**: `tests/test_settings_
  startup.py:153` reconnect test fails in SOME full-suite runs but passes
  isolated; reproduced failing on UNMODIFIED baseline 6c1dc3c too. If the
  owner sees it, it is not a regression — worth a timing look someday.
- **Constrained files** (size-ratchet ceiling, trailing-comment-only):
  shell.qml, ShellState.qml, Theme.qml, desktop_backend.py, battery_saver,
  bluetooth_agent, clipboard, equalizer_actions, ControlDashboard,
  BehaviorPage, TopBarPage, 18 large tests. Their deep documentation lives
  in the map, not in headers.
- Also this session: studied obra/superpowers → `knowledge/superpowers.md`;
  annotation skill + wait2.py tool added to this archive.

## Session 2026-11-08 (evening): island prewarm + warm render + morph reversal (PR #110 OPEN)

User report after testing #109-era main ("VERY GOOD, sắp đạt mức ready for
release"): (1) activity island still not smooth on FIRST open — maybe some
other fly-in panels too; (2) pressing open + ESC nearly simultaneously makes
the island look stuck ("kẹt") then close — function fine, visually not.
User asked: "Có thể khắc phục tất cả bằng cách render sẵn bên ngoài rồi fly
in/out khi được trigger chăng?" (pre-render off-screen, fly in/out on
trigger?).

### Root causes

1. **First open cold** — the island is keepAlive-retained but NOTHING builds
   or renders it before the first trigger: async incubation dead window +
   cold first render (glyph/atlas uploads) mid-flight. #107/#109 fixed
   exactly this for the CC only; the island got nothing.
2. **ESC race = morph asymmetry (spring mode only)** — width/height spring
   targets were `mounted && !dormant ? expanded : compact`, so a close fired
   mid-expansion reversed the flight springs but the island KEPT GROWING
   while leaving → reads as stuck half-open, then snaps away. Non-spring
   mode already followed `expansion` (progress) and reversed fine. Fix:
   targets now follow `mounted && (shown || warmupActive)`.

### PR #110 `perf/island-warmup-flight` @ 4e9488a (OPEN)

- Island prewarm Timer at 6.5 s (staggered after the CC 4 s burst), guarded
  like the CC's; island warm-up Connections mirror the CC wiring; viewport
  reserves the island frame during `warmupActive`; `surfaceLive` EXCLUDES
  the warm pass so the overlay stays the 1×1 sliver (no scrim-window map,
  no blur region) — the #109 "viewport only" principle preserved.
- Island warm pass snaps size springs to FULL open geometry (springs would
  still be mid-expansion during the ≥3 forced frames) and rewinds to
  compact after; `visible: mounted && (!dormant || warmupActive)` — an
  invisible (visible:false) item renders NOTHING into a layer.
- SlideLoader hardening: busy stage DEFERS the warm pass (pending kept;
  all-closed signal + every quiet park retry) instead of dropping it; a
  real open during the pass calls warmupPark() first so the entrance still
  plays the full flight, then retires the warm-up; onLoaded/onShownChanged
  mark `controlWarmupDone` when the tree renders live (no redundant
  invisible passes after a real open).
- PopupElasticity: `warmup` property; `rendering` true during the pass so
  jelly-v2 keeps layer.enabled live (warms the shader path too).
- `LME_SHELL_NO_PREWARM=1` env opt-out, set in release_session_fixture
  (used by BOTH the release-session and render-lifetime suites — they
  measure steady-state memory/lifetimes; the startup burst would pollute).
- **Fixed 3 gated suites stale since #105's keepAlive** (they waited for
  unmount): popup-motion test1 (idle check now reads surfaceLive, close
  wait `dormant and not visible`), popup-motion test2 island wait
  (`islandDormant`), popup-entry (`mounted` key = liveness =
  `mounted && !dormant`), release fixture (`mounted`/`activityMounted` =
  liveness). These would have failed the next gated run on the desktop
  regardless of #110.
- Tests: IslandFlightSourceCase (4 headless source regressions) +
  IslandFlightQmlCase (2 gated: mid-flight-close reversal, warm-pass
  geometry/park/reopen). Ratchets shell.qml→301, test_popup_motion.py→357.
  check.sh green except the 3 pre-existing quickshell-absent errors
  (fail identically on clean main in GLM's sandbox).

### Session ops notes (important for next session)

- **This session did NOT use the remote OpenCode agent** — the gateway
  credentials live only in the user's bootstrap message and were not
  re-supplied; GitHub was directly reachable from the GLM sandbox instead
  (clone + push + PR via REST, token at /tmp/.ghtoken, origin URLs embed
  it — local only). The repo clone is at
  /home/z/my-project/repos/lme-fedora-niri-qs, branch
  perf/island-warmup-flight; archive at repos/GLM-sessions-sandbox-archive.
- Live-machine validation (wf-recorder flights, qt.scenegraph.time) NOT
  done this session — no desktop access. The PR body lists user-side
  checks. If the gateway credentials arrive again, drive the desktop
  agent to: checkout the branch, run the gated battery
  (LME_TEST_MOTION_UI=1; the three repaired suites), record a first-open
  flight + an open/ESC flight, then report.
- PR #109 was MERGED by the owner (3074262) before this session.

## Session 2026-11-08 (afternoon): tab accent race fix (#108 merged) + CC warm-up render (#109 OPEN)

User report: (1) "consider optimizing further — cache more so things look
visually smoother, animations run smoother"; (2) "the initially selected tab
sometimes doesn't render its accent on first open" (Control Center).

### (2) Root cause — CONFIRMED live, 5/5 traced incubations

`Repeater.itemAt()` is NOT a notifiable dependency. The CC tree always
incubates asynchronously (SlideLoader `asynchronous: true`; #107 prewarm at
t≈4 s): `count` reaches 6 BEFORE delegate 0 exists → the StretchIndicator
`targetItem` binding (`count ? itemAt(tabIndex) : null`) evaluates null and
LATCHES; itemAdded fires later (observed order 5→0) but neither count nor
tabIndex changes → binding never re-runs → indicator invisible forever. In
animatedTabs mode the selected tab's plate is transparent — the indicator IS
the accent. Recovery only when tabIndex changes (user switches tabs). Qt
forum (mbrasser): methods can't NOTIFY when their return value changes.

**Fix (PR #108, merged as 2cf536b)**: Repeater gains `property int
population` bumped in onItemAdded/onItemRemoved; target binding references
it (`tabRepeater.population; return ...itemAt(tabIndex)...`) + `tabIndex >=
0` guard. Applied to ControlCenter.qml AND SettingsView.qml (same latent
race in the settings sidebar). Regression test in test_selection_lens.py
asserts the pattern + absence of the racy `count ? itemAt(` form.
Validated: prewarm 6/6, cold 3/3, in-shell settings 3/3 (indicator visible
+ accent pixels), check.sh 1067 OK, zero binding loops. Live checkout
verified post-merge (accent present on first tab, probe-free pixel check).

**Gotcha found**: `toggle settings` IPC in non-demo starts the STANDALONE
settings app (settingsProcess), not the in-shell SettingsPanel — both use
SettingsView so the fix covers both, but in-shell verification needs
`panelKind="settings"; settingsOpen=true` (temp IPC).

### (1) GPU warm-up render (PR #109 `perf/cc-warmup-render` @ 0e7bee4, OPEN)

After prewarm incubation parks the tree it has NEVER rendered → first open
pays glyph raster + atlas/texture uploads mid-flight. PR #109 adds a
once-per-session INVISIBLE render pass: viewport reserves the CC open frame
(viewport ONLY — surfaceLive/scrim/blur/mask/focus stay inactive), tree at
open geometry in `layer` at opacity 0, ≥3 forced frames (FrameAnimation),
then exact park restore (verified: mounted/dormant/warmupDone=true,
surfaceLive=false, exitX≈1262). Skips when !Theme.animations or panel open.
Ratchets shell.qml cap 271→269. SlideLoader gained
controlWarmupPending/warmupActive/controlWarmupDone + warmupShow/warmupPark.

Measured (qt.scenegraph.time.*): first-open glyph 10→6, atlas 398→238,
upload 403→241; warm-up burst at t≈4–5 s with no panel open (atlastexture
18×18…203×90); invisible (wf-recorder CC-region diffs flat); RSS +0.9 MB
noise; island↔CC swap fine. Flight smoothness: arrival 467→417 ms,
mid-flight discontinuities 6→3. HONEST limits: partial effectiveness
(layer+opacity-0 ≠ full on-screen path; pure opacity-0 does NOTHING — the
layer is essential); render>4ms not eliminated (3–5 frames, 7–8 ms);
shader/canvas-FBO attribution unverified; dim→arrival not re-timed.

### Machine state after session

- Live checkout: **main @ 2cf536b** (PR #108 merged), clean, shell running
  (PID 136920, setsid restart with own stderr wrapper /tmp/qs_phase_d.log),
  IPC verified.
- PR #109 open, NOT merged, NOT checked out (owner review).
- Artifacts on desktop /tmp: gap1_set*.png (settings indicator), gap2_*.log/
  mkv (warm-up profiling + flights), c1_*.json (flight analysis), phase_d_*
  (merged-main smoke). pra_*/prb_* from phase B.
- OpenCode session this topic: ses_e4624e17fffeRaAe635CCj7j3b.


## Session 2026-11-08 (midday): PR46-vs-main A/B + prewarm PR #107 (since MERGED by owner)

User premise: "shell dạo này khựng, chắp vá, chưa mượt; PR #46 era was
smooth/stable — find out why the new one is less optimized."

### The A/B (same machine, same settings.json, back-to-back checkouts)

| metric (live) | pr-46 @ 6a73716 | main @ bfab786 |
|---|---|---|
| idle quickshell CPU (ambient on) | **16.4%** | **5.2-5.7%** |
| idle niri CPU | 19.6% | 16.7% |
| ambient render rate | ~116 fps (every vsync) | ~41 fps (#101 budget) |
| idle with desktopShapes=false | n/a | **0.37%** quickshell |
| island-open flight CPU | 81-83% core | 63-73% |
| wifi-open flight CPU | 87-89% | 73-78% |
| reopen burst CPU | 113-116% | 94-107% |
| GUI polish stalls >8ms | 7 (max 17ms) | 0 (max 8ms) |
| RSS | 244 MB | 271-326 MB (retained trees) |
| panel open latency | every open = cold sync mount (windows show ~1-1.5s creation gaps; #104-era stalls) | reopen ~10ms; cold CC 460ms / tray 620ms / EQ 130ms (async incubation) |

**Conclusion: main is equal or better on every objective metric.** The
user's perception is real but not raw perf. Root causes of the FEEL:

1. **Cold-open dead window** (the fix, PR #107): first CC open after every
   login = scrim dims → 300-450 ms nothing → whoosh. Partial-feedback-then-
   stall reads laggier than PR46's single freeze. Prewarm timer (4s after
   start, dormant=true before mounted=true so surfaceLive stays false)
   → first open 460→**33 ms**, no scrim flash, +132 MB RSS at t=4s
   (same steady state keepAlive converges to anyway).
2. **Motion-feel changes since #90** (lens2 timings, StretchIndicator,
   deformation) — different ≠ worse, but reads as "less smooth".
3. **Bug cadence**: 60+ PRs of glass/EQ churn since #46 = daily visible
   glitches; PR46 was the last "quiet" state. "Chắp vá" is about polish
   cadence, not architecture.
4. Ambient is a luxury: 12 shapes cost 5.2% quickshell + ~2% niri 24/7
   (measured on/off); drift is 5-27 px/s = sub-pixel per update at 41 fps
   → the #101 budget is visually fine (do NOT revert it).
5. niri non-xray blur does NOT drop during layer-surface flights —
   VERIFIED empirically (wf-recorder + per-frame region edgeVar: blur
   stays active while panels fly). The upstream "disappears during
   animations" limitation applies to niri's own window animations only.

### Also found

- **main was RED**: `check_architecture.py` size caps — ShellState.qml 261
  and shell.qml 255 nonblank > 250 default, grown by #104/#105 without
  ratcheting. Ratcheted to 261/271 in PR #107's second commit (verified
  main fails, branch passes; full check.sh green on branch).
- `lme-shell.log` tail is misleading: stderr is block-buffered when
  redirected → file growth ≠ activity; log can sit frozen at high CPU.
  For measurement channels, redirect to a dedicated file yourself.
- LiquidButton.qml:37 "Binding loop detected for property color" ×2 at
  startup (cosmetic, unfixed). 7× stale 'yieldOpacity' ShaderEffect
  warnings in the boot log (uniform gone since #96; source has zero
  references — origin unclear, likely stale qml cache; cosmetic).
- desktopentry "Illegal escape sequence" warnings ~2.7/min (swappy's
  .desktop exec string) + firefox MPRIS Position property errors —
  noise, no perf impact found.
- PR46 on this machine has a fragile singleton import chain
  (FeatureBootstrap→…→GlassState→GlassBackdrop) that fails on live
  reload (fixed later by #71's ordering) — a spontaneous reload while
  testing pr-46 left its watcher dead; harmless for measurement.

### Machine state after session

- Live checkout: **main @ bfab786**, clean; shell restarted normally
  (PID from 13:08 restart), IPC verified (`restartBackend` → true).
- settings.json: unchanged from session start (desktopShapes=true,
  liquidGlass tint #b5465668 opacity 0.25 rim 2.0 edgeWidth 0.55 grain
  0.08 passes 2 offset 1.0, barBlur/popupBlur/glassSelection on).
- PR #107 **open, NOT merged** (review gate): branch perf/panel-prewarm
  (2 commits: prewarm + arch ratchet). Machine NOT left on the branch.
- Test artifacts on desktop /tmp: ab_measure*.log, rt_*.log (render
  timing slices), fp_*.json (frame analysis), flight*.mp4 + pw*.jpg
  (flight videos), check_prewarm2.log (green battery). Measurement
  scripts: /tmp/ab_measure.py, /tmp/rt_analyze.py, /tmp/flight*.sh.
- pr-46 branch exists in the desktop repo (fetched for the A/B).

## Session 2026-11-08 (early AM): panel interaction audit — PR #105 merged

User report after #104 ("almost smooth now"): (1) clicking Activity Island
opened BOTH the island and the control center; (2) fast Settings tab
switching briefly overlaid one tab on another; (3) top-bar → control panel
sometimes skipped the opening animation; "audit the logic harder".

Root causes (all verified live — timed journal probes, gdb stack sampling,
pixel-zone screenshot audits):

- **(1)** `SlideLoader.finishClose` parked retained (keepAlive) panels at
  exit offset 0 = their OPEN position, relying on window unmap to hide
  them. The island kept the overlay window mapped → the dormant CC popped
  back into view beside it. Fix: park at the exit-flight edge (off-screen);
  island got keepAlive too (compact-size rewind on dormancy).
- **(3)** exit offset 0 on reopen also meant NO slide-in (progress-0
  deformation ≈ full size at final position → pop). The park restores the
  slide; content swaps under a shown surface reset the flight likewise.
- **(2)** `SettingsPageHost.dispatch` early-return left a stale incubation
  running; its late onLoaded activated the page the user navigated away
  from. Fix: cancel stale incubations, guard onLoaded by content, hide
  retired pages before deferred deletion. Renamed→`qml/components/PageHost`
  and reused for the CC dashboard (no more tab-switch blank flash).
- **NEW logic bug found in audit**: control-tab gestures (audio/devices/
  agenda/system) selected the tab then togglePanel'd — closing an
  already-open CC. Now they only open when closed.
- **THE deep one — ~1s hitch on every panel reopen**: mapping the overlay
  PanelWindow with a retained tree in the scene re-attaches every item to
  the fresh surface (~0.7–1.0s main-thread block; gdb: diffuse QV4 binding
  churn + GC + QQuickCanvasItem Context2D rebuilds; hiding via Item.visible
  moves the same cost to the visibility toggle — do NOT hide big dormant
  trees with visible). Fix: the overlay layer surface stays mapped for the
  whole session (idle = 1x1 transparent sliver, mask null, blur gated by
  new `surfaceLive`); resizes are incremental, no scene teardown.
  **Reopen IPC→slide: ~1000ms → ~10ms.** Island reopen ~11ms retained.
- Atomic swaps: `ShellState.panelSwap` bumped on replacement → shell
  `snapOut()`s the outgoing surface — one popover on stage at a time.

Perf-measurement recipe that worked: `console.warn(Date.now())` probes
chained IPC → togglePanel → onShownChanged → move(), journalctl
`-o short-precise`, plus `gdb -p PID -batch -ex "thread apply all bt"`
sampled in a loop during the block. Remove probes before commit.

OPS LESSON: quickshell's file watcher DIES after a failed config load —
after any mid-edit reload failure, `systemctl --user restart
lme-shell-perf.service`. Order edits: move/renamed files BEFORE files
that reference them. `touch` alone may not retrigger; rewrite same
content does not either after a failed load.

User-side checks pending: eyeball island↔CC swaps (should be instant,
one panel on stage), panel reopen slide-in, CC tab switches (old tab
stays until new loads), Settings tab mashing (no wrong-tab flash).

## Session 2026-11-07 (late): issue triage — 8/8 closed, main green

User directive: "hãy xem các issues và xem xét giải quyết hoặc close
issue" (review the issues; resolve or close). Outcome — every open issue
is now closed, 0 remain:

- **#64, #65, #66 (items 1–2), #67 (bulk), #94 (items 1/3/4)** were
  ALREADY fixed on main by earlier audit-bot commits (c847cec, 1c59140,
  870e001, glass PRs) but never closed — verified each acceptance
  criterion against live main first, then closed with evidence matrices
  (lesson 37). G0 baseline on main: 1064 tests OK.
- **#94 (items 2/5)** — PR #98: the stale `duration: root.forward ? 200`
  assertion fixed structurally AND `Lens2SourceCase` un-gated from
  `LME_TEST_PERSONALIZATION_UI` (a pure source test hidden behind an
  OpenGL gate is exactly how drift survives); qmllint exit-255 quirk
  documented in VALIDATION.md.
- **#66 (item 2)** — PR #99: `CaptureSnapshotIsolationCase` regression
  (snapshot embeds `dict(capture.state)`), PLUS the discovery repair:
  `action_registry_async.py` doesn't match `test*.py`, so BOTH regression
  suites in it (incl. the item-1 `UnexpectedCompletionCase`) were dead
  code in G0 — now imported by `test_action_registry.py` (lesson 38).
  1066 tests after.
- **#67 (item 7)** — PR #100: re-pinned AUDIT.md pkexec line (1317→1306).
- **#92** — PR #101, the big one: reproduced 10.0% idle; backend
  SIGSTOP A/B proved the 84 KB/2 s snapshot pipeline costs ~nothing;
  gdb 120-sample stack sampling showed all threads parked ~97% (wakeup
  frequency, not compute); root cause = `DesktopAmbient` runs
  `MediaAmbient { playing: true }` on an always-visible full-screen
  Bottom layer, drifting 12 shapes at every vsync 24/7. Fix: ~22 ms
  frameTime-accumulation budget (≈30 fps @ 60 Hz, refresh-rate
  independent, exact motion speed). **Measured 10.0% → 5.75% (−43%)**
  after shell restart; per-thread table posted in the issue (lesson 39).
- **#2** — PR #102: fresh previews (5 refreshed + desktop/equalizer/
  liquid-glass new; VLM-verified content), embedded in GLASS.md +
  EQUALIZER_UI_PATTERNS.md.
- **#1** — 23 s demo video (wf-recorder VP9, panel tour) published as
  release `shell-demo-2026-11` asset + issue closed. wf-recorder notes:
  libx264 absent → default VP9; `-d` duration flag absent → nohup +
  kill -INT; `niri msg` has no `--socket` flag → use NIRI_SOCKET env.

Shell restarted once (main @ 0320661); user session verified intact
afterwards (4 windows, no stray capture processes). Live idle: 5.75% of
one core. User's liquidGlass.opacity still 0.0 (from #95 testing).

## Merged through PR #97 (`19f1cbf`) — pill shadows

- #97 `fix(bar): reserve the pill shadow envelope inside the bar layer
  surface` (b3c5469): bar pills' drop shadows no longer clip at the
  layer-surface edge.

## Superseded section: PR #96 (was "awaiting owner review")

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
- live checkout on `main` (#105 merged; service `lme-shell-perf.service`
  runs the deployment quickshell, auto-reloads on file change)
- qsb tool: `/usr/lib64/qt6/bin/qsb` (qt6-qtshadertools 6.11.2)
- bar reserves exclusive zone: app windows start BELOW the bar strip — the
  wallpaper sky is genuinely what is behind the bar pills (pixel-hue
  analysis, 2026-11-07 night; matters when interpreting screenshots)
- niri 26.04 IS the latest stable (2026-04-25; repo moved to the niri-wm
  org). Full capability snapshot + layer-rule/blur reference:
  knowledge/niri.md. main = 26.04 + 264 unreleased commits (max-bpc, stylus
  binds, …) — do not design against them

## User-side checks still pending (tell the user, don't assume)

- **#105 (merged, running live)**: eyeball (a) island↔control-center swaps
  — the outgoing panel should retire instantly, never two panels on stage,
  never the dormant CC reappearing; (b) top-bar → control panel reopen —
  should slide in from the right edge every time, no pop, no dead hitch;
  (c) mashing Settings sidebar tabs — no wrong-tab flash, no overlap;
  (d) CC tab buttons/gestures — old tab stays visible until the new one
  lands; the audio/devices/agenda/system bar gestures no longer close an
  open control center.
- EQ real-machine check (band drag, Apply, presets, Dynamic EQ, Audio view)
- #77: hover/glint feel (ydotool missing on the machine)

## Update protocol
