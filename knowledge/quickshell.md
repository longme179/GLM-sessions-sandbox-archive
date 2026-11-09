# Quickshell — verified capability snapshot

> Refreshed: 2026-11-09 · Clone: `outfoxxed/quickshell@9b0f339` (master, 2026-10-21) at
> `/home/z/my-project/repos/quickshell` (sandbox) · Latest stable: **0.3.2** ·
> User's machine runs **quickshell-0.3.2-1.fc44** (Fedora COPR errornointernet/quickshell,
> verified via `rpm -q` on the desktop; `/usr/bin/quickshell` + `/usr/bin/qs`;
> Qt 6.8.2 runtime, QML modules under `/usr/lib64/qt6/qml/Quickshell/`).
> Purpose: ground truth for `lme-fedora-niri-qs`'s QML-first migration plan
> (`docs/QML_FIRST_MIGRATION_PLAN.md` §3).

## 1. Facts my training data gets WRONG

| Training belief | Reality (verified) | Evidence |
|---|---|---|
| "Quickshell has no Bluetooth API" | **Wrong.** `Quickshell.Bluetooth` exists since **0.2.0**: `Bluetooth` singleton (defaultAdapter, adapters, devices), `BluetoothAdapter` (enabled, discoverable, discovering, pairable + timeouts), `BluetoothDevice` (name, address, state, connected, paired, trusted, blocked, **per-device battery**, `connect()/disconnect()/pair()/cancelPair()/forget()`) | `src/bluetooth/bluez.hpp:63-76`, `adapter.hpp:57-89`, `device.hpp:55-122`; changelog `v0.2.0.md` "Bluetooth Module" |
| "Quickshell has no NetworkManager bindings" | **Wrong.** `Quickshell.Networking` since **0.3.0**: `Networking` singleton (devices model, wifiEnabled, connectivity + check), `NetworkDevice` (networks, state, nmManaged, autoconnect), `WifiNetwork` (signalStrength, security, **`connectWithPsk(psk)`**), `WifiDevice` (scannerEnabled, mode), `Network.connect()/disconnect()/forget()`, **`NMSettings.read()/write(settings)`** for saved-connection/hotspot editing | `src/network/qml.hpp:79-114`, `wifi.hpp:17-67`, `nm/settings.hpp:22-50`; changelog `v0.3.0.md` "Added network management support" |
| "File IO is manual / no atomic writes" | `Quickshell.Io.FileView` has `atomicWrites`, `watchChanges`, preload, `FileViewAdapter` + a JSON adapter class for structured data | `src/io/fileview.hpp:164-324`, `jsonadapter.hpp` |
| "No unix-socket client for IPC" | `Quickshell.Io.Socket` (Q_PROPERTY `path`, `connected`, `write()`, `flush()`, DataStream parsers) — usable for the niri IPC socket (`$NIRI_SOCKET`); also `SocketServer` with a QML handler component | `src/io/socket.hpp:20-43,95-114` |
| "Desktop entries must be parsed by hand" | `Quickshell.DesktopEntries` singleton in core: `applications` object model, `byId()`, `heuristicLookup(name)`, per-entry name/icon/comment/exec/command/categories/keywords/actions + `DesktopAction.execute()`, live monitor on file changes | `src/core/desktopentry.hpp:50-313` |
| "Battery service is read-only percentages" | `Quickshell.Services.UPower` gives `displayDevice`, `devices`, `onBattery`, per-device energy/capacity/changeRate/timeToEmpty/timeToFull/healthPercentage/isLaptopBattery/nativePath **and** `PowerProfiles` (available profiles, current, holds incl. performance degradation reasons) | `src/services/upower/core.hpp:65-80`, `device.hpp:115-162`, `powerprofiles.hpp:107-127` |
| "Pipewire bindings are volume-only" | `Quickshell.Services.Pipewire`: nodes/links/linkGroups models, `defaultAudioSink/Source`, **`preferredDefaultAudioSink/Source` (settable)**, `PwNodeAudioIface.muted/.volume` writes, peak monitoring, link-group trackers for routes | `src/services/pipewire/qml.hpp:56-231` |

**Still true (confirmed):** no generic D-Bus *client* API is exported (internals only —
`src/dbus/` powers Bluetooth/Networking/DBusMenu); no HTTP client object (use QML
`XMLHttpRequest`; QtNetwork is installed); `Process` is destroyed with **SIGKILL** by
Quickshell 0.3.2 — long-lived children need parent-death-signal helpers or
`startDetached()` + explicit cleanup (live regression documented in lme
`docs/CODE_REVIEW.md`).

## 2. Installed module surface (0.3.2 floor, from the desktop)

`Quickshell/` (core: ShellRoot, PanelWindow, Variants, Reloadable, DesktopEntries,
SystemClock, ElapsedTimer, LazyLoader, ScriptModel, IpcHandler…), `Quickshell.Io`
(Process, Socket, SocketServer, FileView, DataStream parsers), `Quickshell.Wayland`
(WlrLayershell, **ScreencopyView** with `live`/`paintCursor`/`captureSource`,
**idle-inhibit + idle-notify**, background-effect blur, toplevel, session lock,
shortcuts-inhibit, activation tokens), `Quickshell.Widgets`, `Quickshell.WindowManager`,
`Quickshell.X11`, `Quickshell.Hyprland`, `Quickshell.I3`, `Quickshell.DBusMenu`,
`Quickshell.Bluetooth`, `Quickshell.Networking`, `Quickshell.Services.{Greetd, Mpris,
Notifications, Pam, Pipewire, Polkit, SystemTray, UPower}`.

## 3. Release timeline (changelog/ in-tree)

- **0.1.0** — initial public.
- **0.2.0** — Bluetooth module (BlueZ, authenticated pairing via agent); D-BusMenu fixes.
- **0.3.0** — network management (NetworkManager D-Bus), popup focus grabbing, IPC signal listeners.
- **0.3.1** — (changelog file exists; see repo for details.)
- **0.3.2** — Qt 6.12 support; fixes: networking state after NM restart, PipeWire route
  volume writes without volume step, `Socket` reconnect after failed attempt, open-wifi
  security display, crash fixes (pam subprocess, session lock reentrancy, async Loader
  teardown).
- **master (unreleased, `9b0f339`)** — SystemTray activation tokens; ScriptModel role
  updates; Hyprland workspace ids; ScreencopyView unplug crash fix; qmlls/qmllint types
  for Qt 6.12; Pipewire event-loop thread fix.

Design rule: the **user runs 0.3.2** — treat master-only features as unreleased and
never design against them (same rule as the niri snapshot).

## 4. lme-fedora-niri-qs integration notes

- Already native in the shell: Mpris, Notifications, SystemTray, Polkit, Pipewire (one
  import), Wayland layershell/background-effect.
- Still wrapped in the Python backend but natively replaceable: audio state (wpctl →
  Pipewire), battery/AC/power profiles (sysfs+powerprofilesctl → UPower/PowerProfiles),
  bluetooth (bluetoothctl → Bluetooth), wifi/nmcli → Networking, desktop-entry scanning
  (custom parser → DesktopEntries), niri event stream (niri_events.py → Io.Socket),
  /proc monitoring (system_monitor.py → FileView), idle inhibit (idle_control.py →
  Wayland idle-inhibit). Full matrix with file:line sources:
  `docs/QML_FIRST_MIGRATION_PLAN.md` §3 in the lme repo.
- Traps carried into the plan: Process SIGKILL orphans (clipboard watchers), hotspot/AP
  mode and secure pairing need real-session checks, Preferences lock/merge semantics
  have no direct FileView equivalent (single-writer via IpcHandler proposed).

## 5. Sources

- Clone `git@github.com:outfoxxed/quickshell` @ `9b0f339` (sandbox
  `/home/z/my-project/repos/quickshell`): `src/{bluetooth,network,io,core,services,
  wayland}/`, `changelog/v0.2.0.md`, `changelog/v0.3.0.md`, `changelog/v0.3.2.md`,
  `changelog/next.md`.
- Desktop probes (2026-11-09): `rpm -q quickshell` → `quickshell-0.3.2-1.fc44.x86_64`;
  `quickshell --version`; `ls /usr/lib64/qt6/qml/Quickshell*`.
- Cross-check: changelog grep for "bluetooth" (v0.2.0) and "network management"
  (v0.3.0) agrees with the installed module directories.
