---
name: quickshell-instant-ui
description: Diagnose and remove open-time latency in a Quickshell shell by retaining panel and page instances, warming the first render offscreen, anticipating on hover, and bounding caches. Use when a panel, control center, settings page, or tab switch shows a loading interval, or when asked to preload/cache UI in a QML shell.
---

# Instant panels and settings in Quickshell

Use this skill when the user says a panel/tab/page "still loads", "opens
slowly", or asks for preloading/caching in a Quickshell shell. Verify the
engine version first; several common fixes depend on it.

## 1. Root-cause checklist (read the code, not the animation)

1. **How many panel trees can stay built?** Find the panel host. A single
   `Loader`/`SlideLoader` whose `sourceComponent` changes per panel keeps only
   the last panel; switching to another panel destroys the previous tree.
   Look for `keepAlive`, `retainedContent`, `onContentChanged`,
   `sourceComponent = null`.
2. **How many pages can stay built?** A two-loader host (`current` +
   `incoming`) is staging, not a cache. A third page destroys the first; a
   later return rebuilds it. Look for `active = false; sourceComponent = null`.
3. **Does the surface process survive close?** If Settings is a separate
   Quickshell process and `onClosed: Qt.quit()`, every reopen pays a cold QML
   engine + backend + page host. Check the shell's launcher script for IPC
   reuse; it only helps while an instance is alive.
4. **What does prewarm actually warm?** A fixed startup timer for one panel is
   a special case, not a policy. Check readiness gating, other panels, hover
   anticipation, and whether the warm pass renders frames or only creates
   objects.
5. **Is the click path doing data work?** Grep `onVisibleChanged`/
   `Component.onCompleted` for `run(...)`, `Process`, timers. Separate a
   blocking fetch from a no-op cache invalidation + poll.
6. **Is the disk/QML bytecode cache real on this engine?** Do not assume.
   Probe the binary's pragmas and whether `.qmlc` files appear. A cold process
   recompiles user QML when the disk cache is disabled; an in-process page
   recreation does not recompile.

## 2. Reference mechanisms (source-verified 2026-11-24)

| Shell | Mechanism | Evidence |
|---|---|---|
| DMS | Prewarm the component type on hover with `Qt.createComponent(url, Component.Asynchronous)`; instantiate on open. Closed surfaces unload after a grace (`Timing.holdMedium`). | `PopoutService.qml:82-145`, `SurfaceWidgetFactory.qml:187,264,387,777` |
| DMS | Settings page hosts: `_cache` + `_cacheOrder`, `_takePage` creates at `x=pageStack.width`, warm/lay out out of sight, LRU `pageCacheLimit=6`, `anticipate()` after 90 ms, teardown one card per 50 ms, `StackView.onRemoved: _release(host)`. | `SettingsContent.qml:233-316,379-437,559-604`; `SettingsMetrics.qml:90-97` |
| Caelestia | All panel wrappers resident inside one layer-shell `ContentWindow`; heavy launcher/dashboard content behind a `Loader` that unloads on close. | `shell.qml:43-45`, `Drawers.qml:20`, `Panels.qml:41-155`, `launcher/Wrapper.qml:25-52` |
| end4 | Whole panel family loaded at startup via `LazyLoader active: Config.ready`; small popups use `FadeLoader` (`active: opacity > 0`) and unload on hide. | `shell.qml:44-58`, `PanelLoader.qml:6-8`, `FadeLoader.qml` |
| Serpantinum | Hidden `preloaderContainer` + `widgetCache`; `ensureWidgetItem` creates once; switches `StackView.replace(cachedItem)` and toggles siblings invisible. | `Main.qml:351-388,673-750,797-804` |
| Quickshell | `LazyLoader` builds in frame gaps; `loading: true` starts background work, `active: true` forces (blocks), `active: false` destroys; `Variants` breaks async. | `src/core/lazyloader.hpp:12-84` |

DMS/Caelestia/end4/Serpantinum commits: see `knowledge/reports/2026-11-24-lme-instant-ui.md`.
Do not copy their cache constants; they are reference values, not measurements.

## 3. Implementation recipe

### Panel pool

- One retained `SlideLoader` per panel kind, created lazily, `keepAlive: true`.
- Active loader `shown: true`; others `shown: false` and parked by the
  existing exit/edge transform.
- Warm a new loader with the existing invisible pass: set
  `retainedContent`, `mounted = true`, `dormant = true`,
  `controlWarmupPending = true`, then trigger `startControlWarmup` from
  `onLoaded`/`onDormantChanged` (it needs a loaded item).
- Bound retention: heavy LRU (start with 2), light panels for the session,
  async eviction (one per ~50 ms) while quiet, never evict the active loader.
- Keep the overlay layer surface mapped and shrink it to 1x1 when idle;
  re-mapping re-attaches retained items.
- Union only mounted, non-dormant loader rectangles for the blur viewport;
  use the active item for the panel blur region; keep the full-content input
  mask so click-outside still closes.

### Page cache

- Keyed host map (string key, not component identity; catalog pages can share
  one wrapper component).
- Create host at `x = stage.width` (past the clip) or at `x=0` with `opacity:0`
  + `layer.enabled:true`; run 1-3 frames; park. Keep the previous page visible
  until the new one is `Loader.Ready` if it is a cold create.
- LRU (DMS starts at 6), async teardown one page per ~50 ms, never during a
  transition.
- Anticipate the hovered/focused nav page after ~90 ms; optionally prewarm
  neighbors while the cache has room.
- Preserve Flickable position and focus on re-entry.

### Settings process

Three options, in increasing scope:

1. **Linger**: `onClosed` hides instead of `Qt.quit()`; a timer
   (`LME_SETTINGS_LINGER_MS`) eventually quits. Reopen via the existing IPC is
   then instant. Memory is held while lingering.
2. **Stub**: after the linger window, destroy the view/page cache but keep the
   process/services; rebuild the view on reopen.
3. **In-process**: host Settings as a `FloatingWindow` in the main shell,
   sharing the engine, theme, catalog and backend. Removes the second QML
   engine and backend; lifetime/isolation trade-off.

### Prewarm policy

- Gate on backend ready + theme ready + catalog settled, and run after the
  first stable frame; yield between items.
- Warm Control Center first; then the next most-used panel (island already has
  its own loader); then configured panels.
- Level 1 hover: `Qt.createComponent`/`FeatureCatalog.component` only (cheap).
  Level 2 hover: instantiate a parked tree after ~150 ms and expire it if never
  opened.
- Respect battery saver; skip secondary prewarm there.

### Dormant contract (mandatory)

A parked tree with `visible: true` keeps `visible`-bound timers and animations
running. Multi-retention multiplies that cost. Add a `panelActive`/`pageActive`
property set by the host, and gate clocks, `Timer`s, media/visualizer loops and
`layer.enabled` on it. `SlideLoader` parks off-screen with `visible` still true
on purpose: toggling `Item.visible` on a large retained panel costs ~800 ms in
LME (measured). Do not "fix" the park by hiding the tree. Page-sized trees may
use `visible` after measurement.

## 4. Measurement

- Define open latency as input -> first frame with final content, not the end
  of the entrance animation.
- Instrument with `LME_SHELL_LATENCY_TRACE=1`: state change, host creation,
  `Loader.Ready`, first frame after present, panel open. Parse logs; report
  p50/p95 over 10 runs.
- Headless Sway + software renderer is fine for relative before/after; run the
  final acceptance on the real compositor/GPU.
- Memory: aggregate PSS with `scripts/memory_report.py --label`, 10 s after
  warm; report baseline and delta, not just one PID.
- Idle: one minute with caches parked; require no continuous frame callbacks
  and <=1% of one core delta. A retained clock/visualizer fails the check.

## 5. Traps

1. **Commit subjects lie; bodies don't.** A subject saying "460 -> 33 ms" may
   have a body documenting 460 ms cold / ~70 ms retained. Read the body before
   citing a baseline.
2. **Quickshell 0.3.2 has no user-QML disk cache.** It rejects
   `@pragma DiskCache`/`RenderControl`; `launch.cpp` comments out the cache env
   because qsintercept paths cannot be cached. Probes produced 0 `.qmlc` even
   with `QML_DISK_CACHE=1`/`QML_FORCE_DISK_CACHE=1`. Inside one process,
   recreating a page does not recompile; a new process does. Do not promise
   bytecode-cache wins on 0.3.2.
3. **`Variants` blocks async loading.** Do not put a `Variants` inside a warm
   loader and expect background work.
4. **Visibility propagation is expensive** on large retained panels (~800 ms
   measured). Park off-screen.
5. **Retention without suspension** turns open latency into idle CPU. Audit
   timers before declaring victory.
6. **PageHost is not a cache when it destroys the retired page.** Rapid A->B
   can reuse the incubating B; A->B->C destroys A. Be precise.
7. **A single retained panel is not a panel cache.** Opening another panel
   destroys the previous component tree.
8. **Don't trust a warm path that only creates the object.** Layout, polish,
   shader/pipeline selection and the first frame remain; render 1-3 frames
   offscreen.
9. **Don't copy DMS's 6/90/50 constants** without measuring LME page cost and
   the 400/500 MB budget.

## 6. Verification pattern

Before writing the plan, delegate a read-only check to another agent with a
numbered claim list and require `CONFIRMED / CORRECTED / UNVERIFIABLE` plus
file:line. A verifier caught four overstatements in the 2026-11-24 LME pass
(PageHost reuse of an incubating page, two SlideLoaders, end4 waiting for
`Config.ready`, and the unsupported 33 ms figure). Then spot-check every
correction yourself.

Prompt template: ask for a table (claim, verdict, evidence, correction), a
"what the plan must not claim" section, and no edits to the target repo.

## 7. LME-specific pointers

- Plan: `lme-fedora-niri-qs/docs/INSTANT_UI_PLAN.md`.
- Research: `lme-fedora-niri-qs/docs/INSTANT_UI_RESEARCH.md`.
- Current hosts: `qml/components/SlideLoader.qml` (single panel slot),
  `qml/components/PageHost.qml` (two-slot page staging),
  `qml/settings/SettingsApplication.qml` (process quits on close),
  `shell.qml` prewarm timers.
