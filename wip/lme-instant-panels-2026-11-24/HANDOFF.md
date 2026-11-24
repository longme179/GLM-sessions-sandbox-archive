# HANDOFF — LME instant panels/Settings (session 2026-11-24, STOPPED: out of credits)

Task (owner longme179): opening panels (Control Center...) and switching Settings/Control
tabs still shows a load interval; make it instant. Study famous shells, write a technical
plan, implement, then commit + PR to `longme179/lme-fedora-niri-qs`. Earlier PRs #192/#194
(and their reverts #193/#195) failed; owner said do NOT consult them.
Owner also wants SKILL.md / knowledge saved in this repo. PATs come from the owner's
message, never from files. Nothing was pushed to the LME repo; no PR exists yet.

## Where I stopped (resume HERE)
Working copy: `~/claude's works/lme-fedora-niri-qs`, branch `perf/instant-panels-pages` (off main a38a4e2).
`tests/` there is an untracked COPY of the owner's local suite (from ~/.local/share/Trash/files/lme-191/tests,
the repo gitignores tests/). Uncommitted diff is saved as `wip-instant-panels.patch` in this folder.
DONE (edited, NOT yet loaded/linted/measured even once):
1. `qml/components/PageHost.qml` rewritten: one retained Loader per key (`entries`), `key`, `resolve(key)->Component`,
   `warmKeys` (background async build, one at a time), `active` (hides pages), `pageLoaded(item)` signal, `animate`.
   Requested page builds SYNCHRONOUSLY (asynchronous:false); in-flight async build is switched to sync on demand.
2. `qml/settings/SettingsView.qml` + `qml/panels/ControlCenter.qml` ported to the new PageHost API.
3. `shell.qml`: panelLoader content = one `panelStackComponent` (a PageHost keyed by ShellState.panelKind)
   so every built panel stays alive; prewarm list in warmKeys. Blur region follows `(panelLoader.item as PageHost).item`.
4. `qml/panels/NotificationCenter.qml`: removed dead `onAnnotateRequested` (signal removed in 769b6aa; produced a
   warning "Cannot assign to non-existent property" that surfaced in the feature catalog log). Unrelated, safe, keep.
NOT DONE (in order):
a. Verify it loads: run `python3 tools/lme-latency/measure.py <repo> out.json` (see below); fix QML errors.
   Known risk: `PageHost` `onKeyChanged`/`onResolveChanged` ordering when SettingsView sets key before resolve;
   `item as Item` casts under `pragma ComponentBehavior: Bound`; `Loader.visible` binding uses `root.shown === page`.
b. Check SlideLoader interplay: SlideLoader.onLoaded fires when the stack is ready, NOT when the first inner panel
   is; `rememberedWidth/Height`, `item.implicitWidth` (forwarded in panelStackComponent) and `panel.forceActiveFocus()`
   must still work (focus forwarding added via onPanelOpenChanged; verify Escape closes, launcher search focuses).
c. Dormant contract: hidden panels are `visible:false` inside the stack (small trees only) but SlideLoader parks the
   WHOLE stack off-screen with visible:true on purpose (toggling visible on a big tree cost ~800 ms). Audit timers:
   NotificationCenter (60 s clock), DisplayPage/IdlePage/NightLightPage (`running: root.visible`) are now gated by
   PageHost `visible:false` — good; SettingsView timer (1 s, display preview) only runs while status applying.
   BluetoothState.watch in DeviceControls uses `visible && nativePairing` — still correct.
d. Settings PROCESS: `SettingsApplication.qml:52,58` `onClosed/onCloseRequested: Qt.quit()` => every reopen is a cold
   process (~1 s). Plan: hide instead of quit + linger timer (`LME_SETTINGS_LINGER_MS`, default e.g. 90 s) and set
   SettingsView `active:false` while hidden. `scripts/settings.sh` already reuses a live instance via IPC `openPage`.
   NOTE `FloatingWindow visible` is bound to `view.status===Ready`; needs a separate `shown` flag. Memory target
   400/500 MB (AGENTS.md): a lingering Settings costs one QML engine + python backend.
e. Re-measure (numbers below), run `./scripts/check.sh` (baseline: 1500 tests, 9 FAIL = environmental, see below),
   `./scripts/run-gates.sh --gates G0` (+G1/G2/G3 for QML changes), 10-cold-launch rule from AGENTS.md if feasible.
f. Write `docs/INSTANT_UI_PLAN.md` (technical plan; owner explicitly asked for a heavily technical plan) + update
   docs/STATE.md, docs/MIGRATION_LOG.md (<=30 lines), CHANGELOG.md, docs/WORKSPACE_MAP.md REL tags, and
   `config/architecture.json` ceilings (PageHost rewrite changes line counts; check-architecture ratchet).
   AGENTS.md: separate commits for tests / implementation / docs; replies <= 40 lines; never touch the live session.
g. `git push` branch + `gh pr create` (needs owner PAT from the owner's message; set GH_TOKEN env only).
h. Update `knowledge/lessons-learned.md` (lesson 87) and `skills/SKILL-quickshell-instant-ui.md` with section below.

## Measured baseline (my harness, private headless sway, gles2, 12-core Ryzen 5 7535HS, demo mode)
`tools/lme-latency/measure.py REPO OUT.json [--renderer gles2|pixman]` patches a COPY of the tree with `console.warn("TRACE ...")`
probes + IPC fixtures (tToggle/tTab/tPage), drives the scenario, prints median ms: `ready` (loader finished),
`content` (first frame with content), `settled`, `gap` (worst frame gap). Never touches the live session.
Headless demo on software-ish GL is slower than real GPU: use for RELATIVE comparison only. `LAT_VARIANT=sync`
patches `asynchronous:true -> false` in the hosts (A/B for incubation cost); `LAT_KEEP=1` keeps the temp dir.
Baseline main (base2.json): Control Center first open content=986 ms (prewarm timer already fired; still ~1 s),
reopen ~100 ms, panel->panel switch back to control 888 ms (tree destroyed), tabs: audio 213, devices 372, agenda 535,
monitor 730 ms; second lap IDENTICAL (nothing cached). Settings (in-shell) open 712 ms, pages elements 432,
topbar 1096, notifications 806, behavior 982 ms; some pages already ~0-30 ms because catalog Component compile was cached.
Sync variant (sync1.json): tabs audio 89, devices 381, agenda 273, monitor 739 ms: async incubation roughly doubles
latency for small pages and does not help big ones. => Building synchronously on request + keeping built pages is the lever;
async is only good for background warm.
Component micro-bench (`component-bench.*`, ms per instance): LiquidComboBox 8.1, LiquidButton 4.8, SettingsCard 2.8,
GlassPanel 1.8, IconButton 1.5, GlassMaterial 1.6, ExpressiveSwitch 0.56. A page with 40 buttons ~ 200 ms. Hot spots to
consider later: LiquidButton (GlassMaterial + LiquidFeedback + 2 MotionValue per button), LiquidComboBox.
Live process (owner, real session): quickshell PSS 241 MB, backend PSS 35 MB, idle CPU ~0.06 core at the sampling time.

## Baseline check.sh (clean main + copied tests): 1500 run, 9 FAIL, 185 skipped, 514 s
All 9 are `test_native_display_idle` (argv quoting): the repo path contains an apostrophe ("claude's works") so
`shlex.quote` output differs from the fixture. ENVIRONMENTAL, caused by my work-folder name, not by code. Run checks from
a path without an apostrophe (e.g. `/tmp/opencode/lme`) or compare against baseline. Use `env -u WAYLAND_DISPLAY`.

## Reference-shell findings (all verified in cloned source; clones in `~/claude's works/refs/`, shallow)
- DMS: per-popout `LazyLoader{active:false}`; first click sets active; `PopoutService.prewarm(url)` on HOVER = `Qt.createComponent(url, Asynchronous)`
  (types only); closed popouts unload after `Timing.holdMedium` = 3000 ms; DPopoutHost keeps content `_retainedContent` 3000 ms;
  ONE always-mapped layer surface per screen shrunk to 1x1 when idle (needs fork 'renderControl'/'inputOnly'); SurfaceFrameGate reveals only after
  a frame was committed; `primeContent()` builds+measures before `open()` (dash waits `ready`, 250 ms deadline).
  Settings = in-process FloatingWindow, unloaded after hide; pages = StackView children parked at x=width, LRU 6, hover anticipation 90 ms,
  neighbours prewarmed, teardown one card per 50 ms, page built in 4 ms slices, steps gated on frames.
- Caelestia: one always-mapped full-screen ContentWindow per screen, mask = Subtract of panel regions; wrappers `Loader{active: shouldBeActive||visible}`
  destroyed when `offsetScale==1` (no keep); size fallbacks (`|| 854`) for the first open; services warmed at startup; 500 ms spring hides build.
  Dashboard tabs: Loader per tab active if current or scrolled into view. Settings (Nexus) in-process FloatingWindow destroyed on hide, pages async incubateObject.
- end-4: PanelWindow per panel, unmapped when closed; right sidebar `Loader active: open || keepRightSidebarLoaded` DEFAULT TRUE (~15 MB cost, doc'd);
  left sidebar content created once and reparented; session/cheatsheet fully lazy. Settings = separate process, Loader per page, no cache (like ours today).
- iNiR: 3 loader kinds: PanelLoader / DeferredPanelLoader (waits shellEntryReady 200 ms + deferredPanelsReady 500 ms) / OnDemandPanelLoader
  (`resident = open || keepLoaded`, closeGraceMs 300, `retainAfterUse` + `retainIdleMs` 5 min); settings pages = Repeater of Loaders with LRU cacheLimit 2.
  Note in iNiR: qs: VFS prevents QML disk cache for Loader documents.
- Noctalia: C++ (0 qml); panel objects persist, layer surface + scene destroyed on close, rebuilt on open (no warm cache).
- Quickshell 9b0f339: LazyLoader/Loader async incubation budget = 1/3 frame (`incubator.cpp:129-134`), 2x when render loop lacks interleave;
  NOT configurable from QML. `PanelWindow` visible:false DELETES the QQuickWindow+layer surface (`deleteOnInvisible`), QML items survive;
  re-show = new surface + configure round trip. No `DiskCache` pragma in 0.3.2. `Variants` breaks async. `Retainable` exists only for exit transitions.
Conclusion: nobody "preloads off-screen" exactly; the winning pattern is (1) keep BUILT trees alive (end4 sidebar, DMS 3 s hold, Serpantinum cache),
(2) start the build before the click (DMS hover prewarm, DMS neighbours), (3) reveal only after a rendered frame, (4) park/hide so idle cost ~0.
Owner's guess (preload + cache) is right; the missing piece in LME was multi-instance retention + building synchronously when asked.

## Ideas not yet done (after the above works)
- Hover prewarm: bar button hover => `FeatureCatalog.component(entry)`/`panelStack.entry(kind,false)` (cheap level 1).
- Frame-gate the reveal (DMS SurfaceFrameGate): first rendered frame at final geometry before slide starts.
- Cut per-button cost (LiquidButton/GlassMaterial/LiquidFeedback shared material pool or lazy children until hover).
- Retention budget: measure PSS after warming all panels (limit 400/500 MB); evict heavy panels LRU if over.

## UPDATE 2026-11-24 (second pass) — implementation done, awaiting gates/PR

Branch `perf/instant-panels-pages`, commit `334b57f` (implementation) on top of
main a38a4e2. Final design and numbers: repo `docs/INSTANT_UI_PLAN.md`.
- PageHost = keyed sync Loaders, off-screen park, LRU 6; PanelStage (new
  `qml/panels/PanelStage.qml`) = PageHost keyed by panelKind, LRU 4, permanent
  SlideLoader content, loaded synchronously; 4 s prewarm now completes.
  `SettingsApplication` hides + linger 60 s; `SettingsView.active` gates timers.
- Harness final7.json: first control 115 ms, switch-back 41–110 ms, tab
  revisits 3–20 ms, Settings retained revisits 24–27 ms. First visits stay
  build-bound (tabs 170–760, Settings 105–820).
- Remaining: run `check.sh` on final tree + G0/G1/G2/G3, docs commit, push
  branch + PR. Real-session checks owed: prewarm hitch, Settings re-show via
  niri rules, aggregate PSS (harness demo RSS ~740 MB is not the real total).
- Do NOT use the live session for measurements.

## FINAL 2026-11-24 — branch pushed, PR #196 open

- Branch `perf/instant-panels-pages`: `5ff881e` implementation, `8a2d27c` docs.
  PR https://github.com/longme179/lme-fedora-niri-qs/pull/196 (base main a38a4e2).
- Final harness (final8.json): first Control Center 102 ms, switch-back 84–98 ms,
  tab revisits 0–16 ms, retained Settings page 21–27 ms; demo RSS ~603 MB
  (740 before the duplicate-build fix).
- Fixed during verification: Loader anchors overriding the park x; re-entrant
  `show()` from `onResolveChanged` building the first page twice.
- Gates: check.sh 1500 tests with only the known flaky prefs shutdown timeout
  (passed twice on rerun); qmllint clean; G1–G6 failures are identical on clean
  main in this environment (missing private pointer helper/test modules, stale
  native catalog fixtures, polling snapshot). No gate claimed green beyond that.
- Owed on the real session: prewarm hitch, Settings re-show through niri rules,
  aggregate PSS vs 400/500 MB.
