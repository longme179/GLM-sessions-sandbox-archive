# Qt 6.11.2 / quickshell 0.3.2 measurement facts (Agent-2, 2026-11-25, batch 3)

Verified on the installed host build (`qt6-qtdeclarative-6.11.2-3.fc44`, `quickshell 0.3.2-1.fc44`,
real loader + headless sway + real hardware). Every one of these cost at least one failed attempt.

## QML incubation is NOT time-sliced on this stack

- `Loader { asynchronous: true }` runs the creation through `QQmlIncubator`, and with quickshell
  0.3.2 the incubation controller path is not wired to the render loop: the incubated component
  builds in ONE solid block on the GUI thread (measured 400–850 ms for heavy Settings pages;
  a 4 ms heartbeat Timer starves for the whole block, so it is a real visible freeze).
- The Qt docs' "incubateFor per frame" pacing requires the application to drive
  `QQmlIncubationController`; a plain QML app gets no slicing for free.
- Consequence for designs: `asynchronous: true` is useful as a START gate (decide WHEN a build
  begins, e.g. only while the surface is quiet) and for preemption (drop an incubating object and
  re-queue), but it does NOT protect frame pacing by itself.
- A `Timer` keeps firing during incubation in some builds but the heartbeat gaps prove the GUI
  thread is blocked; do not trust "async" naming — measure.

## Frame signals on Quickshell windows

- `Connections { target: window; onFrameSwapped }` inside a Quickshell `FloatingWindow` NEVER
  fires (the Quickshell window type exposes no frame signal in 0.3.2).
- The working counter: from inside any `Item`, `readonly property var hostWindow: Window.window`
  (attached property, resolves to the real `QQuickWindow`) and
  `Connections { target: hostWindow; function onFrameSwapped() {...} }`.
- Cheap alternative when sampling is enough: count into a property and sample it from a 100 ms
  Timer (this is what the final probe does; the F lines are emitted from the sampled counter).
- `QSG_RENDER_TIMING=1` output never appeared in quickshell's stderr on this build — do not rely on it.

## Qt 6 hover delivery (measured, hover_test.qml)

- Hover goes to the TOPMOST hover-accepting item ONLY. A bottom `MouseArea` with hoverEnabled
  sees the pointer only over blank areas — never over buttons/fields/sliders.
- A non-blocking root `HoverHandler` keeps tracking the pointer over every control (LiquidButton,
  ExpressiveField, LiquidSlider, plain hover Button, hover MouseArea), child hover states still
  work, and clicks still reach the buttons. This is the correct global activity sensor.
- `QQuickHandlerPoint` properties (position, scenePosition, velocity…) are readonly with NO notify
  signals: bind-and-poll does not work; sample them in a function called from a Timer/gate.
- `QQuickHoverHandler` exposes only `hovered`/`blocking`.

## Wayland virtual pointer (private compositors only)

- `zwlr_virtual_pointer_manager_v1` v1: `create_virtual_pointer` is opcode 0 (opcode 1 is destroy —
  sending it kills your proxy with "invalid object"). motion_absolute opcode 1, button 2, frame 4.
- libwayland refuses out-of-order client ids ("no hole-punching"): allocate ids strictly increasing
  (display 1, registry 2, sync callback 3, seat 4, manager 5, pointer 6, then 7+).
- Sway headless (`WLR_LIBINPUT_NO_DEVICES=1`) exposes the manager global; create the pointer
  BEFORE the client starts, or Qt may not create a pointer capability at all.
- `swaymsg seat seat0 cursor move` does NOT reach clients without a pointer device.

## Misc

- The host `/usr/bin/qmllint` is the Qt 5 one (dies on `pragma ComponentBehavior`); the only
  syntax check that counts is running the real loader on a scratch copy.
- `check.sh` baseline is 10 failures now: 9 × test_native_display_idle plus
  test_control_center_prewarms_tab_pages_after_open (stale pinned regex — does not match
  pristine origin/main either). Do not chase that one as a regression.
- Shell on the host expands `$var` in `for` loops sent through the PTY runner: write commands out
  literally, never rely on loop-local variables surviving.
