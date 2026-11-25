## What

Fixes the Settings-app stutter identified in the batch-3 diagnosis: the startup pre-warm (batch 2) built the 17 remaining Settings pages **synchronously on the GUI thread** while the window was already visible and in use — every gap ≥ 100 ms during the first seconds lined up with one of those builds — and each search keystroke re-ran `SettingsRegistry.search()` three times (navigation Repeater model replaced per keystroke, tearing every delegate down and up again).

## How

**`qml/components/PageHost.qml`** — new opt-in `asyncPages` (default false, so `PanelStage` and `ControlCenter` keep their synchronous warm-up unchanged):
- the first page a host shows still builds synchronously (the window must never open onto an empty pane);
- background walk pages incubate through Quickshell's incubator, one page in flight, started only after ~600 ms of surface quiet and never while the host is hidden;
- a page the user requests preempts an in-flight background build (the victim is cancelled and re-queued at the front) and, while it loads, the outgoing page recedes (dims) instead of sitting as if the click had missed;
- a superseded pending request is cancelled.

**`qml/settings/SettingsView.qml`**:
- one shared `results` property per keystroke; the navigation Repeater keeps a constant model and non-matching delegates hide (layouts skip invisible items);
- quiet gate: activity tracking via a non-blocking root `HoverHandler` (sampled — `QQuickHandlerPoint` has no change signals, and Qt 6 hover goes to the topmost accepting item only), `onContentYChanged` on both Flickables, typing and page changes;
- `framesRendered` counter on the real `QQuickWindow` (`Window.window`; the Quickshell window type carries no frame signal) that also counts as activity.

**`qml/settings/SettingsApplication.qml`** — the Settings view `Loader` builds synchronously (incubating it opened a window with an empty content pane for about a second).

## Measured (same scripted session each; full logs in the linked analysis)

| Interaction | main | branch |
|---|---|---|
| Scrolling a page, real hardware | 2312 ms stalled across 12 scrolls (6 freezes ≥ 100 ms) | 160 ms (1), 96.6 fps mean, worst frame 129 ms |
| Worst keystroke in search, real hardware | 212 ms | 1 ms |
| First cold click on a heavy page (wallpaper) | 1071 ms whole-window freeze | 0 ms freeze; page shows after ~1.7 s with the receding cue |
| Cold click `display` (headless) | 481 ms freeze | 0 ms freeze; +307 ms to shown |
| Total GUI-thread stall, first 20 s of use, real hardware | 5987 ms | 2549 ms |
| Longest single freeze during use, real hardware | 869 ms | 468 ms |
| Window opens onto | blank pane ~2 s | first page already there |
| Warm-up completes | ~8.4 s after open (blocking) | ~30 s (quiet windows only, non-blocking) |

Headless numbers are consistent (use-phase stalled 7341 → 2476 ms; first 8 s 5011 → 591 ms).

## Known limitation

The quiet gate only gates *starting* a build; an incubation that has started in a quiet window still blocks the GUI thread for up to ~0.8 s if the user starts interacting mid-build (measured once on `topbar`, once on `elements`). Follow-up options: slice heavy pages into incubated sections, or split the biggest pages (topbar, wallpaper, controlLayout) into lazy sub-components.

## Tests

`./scripts/check.sh`: 1498 tests, 10 failures — the 9 pre-existing `test_native_display_idle` failures plus `test_control_center_prewarms_tab_pages_after_open`, whose pinned regex (`running: root.initialized && root.visible` in ControlCenter.qml) does not match **pristine origin/main either** (0 occurrences); it predates this branch. No new failures from these changes. `tests/` stays untracked per repo convention.

Ref: Agent-2 session notes, journal entry `BATCH3-STATUS-2026-11-25` (Qt 6.11.2, quickshell 0.3.2).
