# 2026-11-24 — LME instant panel/Settings research

Task (owner): opening panels such as Control Center and switching between
Settings tabs still shows a loading interval; make it instant. Clone famous
Quickshell shells, analyze how they preload/cache, and produce a deeply
technical plan. When done: commit + PR to `longme179/lme-fedora-niri-qs`.

## Environment

- Host: `fedora`, user `kimhoanglong`; the Command Code sandbox runs on the
  same filesystem as the OpenCode server (`/api/info` = 2.3.0, hostname
  `fedora`).
- LME Shell repo: `/home/kimhoanglong/lme-fedora-niri-qs`, `main` at
  `f234268` (PR #191 merged). The live config is a symlink
  `~/.config/quickshell/lme-shell -> repo`.
- Installed: Quickshell 0.3.2 (Fedora COPR), Qt 6.11.2, niri 26.04.
- Working docs worktree: `/home/kimhoanglong/lme-worktrees/instant-ui`, branch
  `docs/instant-ui-plan`.

## Verified findings (file:line in the LME repo at f234268)

1. **One arbitrary-panel slot.** `shell.qml:187-195` chooses the panel
   component from `ShellState.panelKind`; `SlideLoader.onContentChanged`
   (`qml/components/SlideLoader.qml:187-189`) replaces `retainedContent` and
   destroys the previous tree. Only the last panel stays warm. ActivityIsland
   has its own retained `SlideLoader` (`qml/panels/ActivityIsland.qml:10,20`).
   Baseline: 460 ms cold arrival, ~70 ms retained reopen (commit `c66dda7`
   body, PR #107); the subject's "33 ms" is not supported by the body. Current
   comment: 300-450 ms incubation, ~70 ms retained (`shell.qml:220-223`).
2. **PageHost is two-slot staging, not a cache.** `qml/components/PageHost.qml`
   `activate()` destroys the retired page (lines 20-33); `dispatch()` reuses
   current/incoming (35-46). A third page destroys the first; a later return
   rebuilds. Used by Control Center (`qml/panels/ControlCenter.qml:19,141`) and
   Settings (`qml/settings/SettingsView.qml:142-167`). Catalog pages add a
   nested Loader (`SettingsView.qml:154-160`).
3. **Settings is a cold process after every close.**
   `qml/settings/SettingsApplication.qml:52` has `onClosed: Qt.quit()`;
   the close path also quits (lines 56-58). `scripts/settings.sh:63-112` reuses
   a live instance via IPC, but a normal close removes it. STATE's ~1.0 s
   Settings launch-to-visible is a cold process measurement. The window is
   only shown when the view is Ready (`SettingsApplication.qml:43`).
4. **Fixed-timer prewarm only.** 4 s for Control Center, 6.5 s for the island
   (`shell.qml:220-250`); no other panel/page, no hover anticipation.
5. **Quickshell 0.3.2 user-QML disk cache is not a lever.** It rejects
   `@pragma DiskCache` and `@pragma RenderControl`; launch.cpp comments out the
   disk-cache env because the engine refuses to cache qsintercept paths
   (`quickshell/src/launch/launch.cpp:91-129,233-242` at `9b0f339`). Probes
   with `QML_DISK_CACHE=1`, `QML_FORCE_DISK_CACHE=1` and an explicit path
   produced 0 `.qmlc`; the live cache had one 688-byte file; the Qt pipeline
   cache (~160 KB) exists. A new process recompiles user QML; an in-process
   page recreation does not.
6. **On-open data work is secondary.** `controlsRefresh` is a backend no-op
   that invalidates caches before the 2 s poll
   (`scripts/desktop_backend.py:1401,1473`); display/idle/equalizer refresh
   natively. UI construction/first render dominates.

## Reference study (pinned commits)

- **DMS** `291f4c5`: `PopoutService.prewarm()` uses
  `Qt.createComponent(url, Component.Asynchronous)` on hover
  (`PopoutService.qml:137-146`; hover sites `SurfaceWidgetFactory.qml:187,264,
  387,777`); closed popouts unload after `Timing.holdMedium` (82-104).
  Settings pages: `SettingsContent.qml` `_cache`/`_cacheOrder` (233-236),
  `_takePage` parks at `x=pageStack.width` (241-270), LRU `_release`
  (273-286), async `_doom`/`_reap` (288-316), `anticipate()` + neighbors
  (379-437), page host + `StackView.onRemoved` (559-604). Constants: cache 6,
  anticipation 90 ms, teardown 50 ms (`SettingsMetrics.qml:90-97`).
- **Caelestia** `1e44367`: modules at start (`shell.qml:43-45`); one layer-shell
  `ContentWindow` per screen (`Drawers.qml:20`); every panel wrapper declared
  in `Panels.qml:41-155`; launcher/dashboard content behind a Loader that
  unloads on close (`launcher/Wrapper.qml:25-52`).
- **end4** `21733c3`: whole panel family via `LazyLoader active: Config.ready`
  (`shell.qml:44-58`, `PanelLoader.qml:6-8`, `IllogicalImpulseFamily.qml`);
  small popups use `FadeLoader active: opacity > 0` (unload on hide). Loaders
  wait for `Config.ready`, not the first frame.
- **Serpantinum** `6e18148`: hidden `preloaderContainer` (351-354),
  `widgetCache` (356), `ensureWidgetItem` (366-387),
  `StackView.replace(cachedItem)` (797-804), siblings visible=false.
- **Noctalia** `b912cad`: C++/Luau (645 `.h`, 576 `.cpp`, no `.qml`); not a QML
  reference.
- **Quickshell** `9b0f339`: `LazyLoader` docs (12-84): background creation in
  frame gaps; `loading:true`; `active` forces/blocks; `Variants` breaks async.

## Deliverables

- `docs/INSTANT_UI_PLAN.md` — root causes, PanelStage/PageHost v2/Settings
  warm-session/prewarm design, retention table, dormant-tree contract,
  phases, measurement, risks, flags, owner decisions.
- `docs/INSTANT_UI_RESEARCH.md` — the reference study with pinned links.
- Docs-only branch `docs/instant-ui-plan`; PR #192 opened against `main`
  (https://github.com/longme179/lme-fedora-niri-qs/pull/192; no runtime change).
  G0 on the docs worktree: 1315 passed / 0 failed / 185 skipped (534 s).
  The implementation phases await owner authorization.

## Corrections from the independent verification session

The remote verifier (`ses_df405eb98ffe0KaRr8gs4Oc8R2`, model
`opencode/beam-free`) confirmed 6/10 and corrected 4:

1. PageHost does not re-instantiate on every switch; it reuses an
   already-incubating incoming page. Only a later revisit of a destroyed page
   rebuilds.
2. `shell.qml` has two SlideLoaders (panel + ActivityIsland); do not call the
   panel host "the only" one.
3. end4 LazyLoaders activate after `Config.ready`, not the first frame.
4. Git #107's subject says 33 ms but the body documents 460 ms cold / ~70 ms
   retained; do not cite 33 ms as a baseline.

It also independently confirmed the 0.3.2 `DiskCache` rejection and the
launch.cpp comment.

## Owner decisions still open

- Panel retention budget (heavy limit 2 starting point vs stricter), page LRU
  limit (6 starting point).
- Settings default: 90 s full linger vs 0 vs stub/in-process.
- In-process Settings prototype (`LME_SHELL_INPROCESS_SETTINGS=1`) yes/no.
- Secondary prewarm list / hover instance warm.
- Separate decision on a Quickshell upgrade with `@pragma DiskCache` (system
  package, not this repo).

## Sandbox/agent notes

- Health check and session API worked; the verifier session used
  `opencode/beam-free` and wrote its report to
  `~/agent-collab/research/verify-instant-ui.md`.
- The new verification tool is `tools/oc_verify.sh` (see `tools/README.md`).
- G0 on the docs worktree needs a symlink to the main checkout's untracked
  `tests/` directory; the worktree alone lacks `tests/migration_checks.py`.
- The sandbox and the OpenCode server share the host filesystem in this
  session; direct file access was used for source reading, while the verifier
  agent ran independently.
