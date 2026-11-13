# Quickshell — verified capability snapshot

> Refreshed: 2026-11-09 · Clone: `outfoxxed/quickshell@9b0f339` (master, 2026-10-21) at
> `/home/z/my-project/repos/quickshell` (sandbox) · Latest stable: **0.3.2** ·
> User's machine runs **quickshell-0.3.2-1.fc44** (Fedora COPR errornointernet/quickshell,
> verified via `rpm -q` on the desktop; `/usr/bin/quickshell` + `/usr/bin/qs`;
> Qt 6.8.2 runtime, QML modules under `/usr/lib64/qt6/qml/Quickshell/`).
> Purpose: ground truth for `lme-fedora-niri-qs`'s QML-first migration plan
> (`docs/QML_FIRST_MIGRATION_PLAN.md` §3).

## 0. CORRECTIONS 2026-11-11 (probed on the owner's desktop, offscreen quickshell)

The "still missing" list below was written from the Quickshell namespace only.
**Qt6's own QML modules are installed too and work inside quickshell** — three
plan blockers fell:

| Capability | Verdict | Evidence (probe E, /tmp/lme-cap-probe) |
|---|---|---|
| Directory listing | **AVAILABLE** via `Qt.labs.folderlistmodel` (`FolderListModel`: folder/nameFilters/showDirs/showFiles/count/get(i,role)) | /sys/class/backlight → 1 (`amdgpu_bl1`), /sys/class/hwmon → 8, /proc `[0-9]*` dirs → 414 |
| SQLite | **AVAILABLE** via `QtQuick.LocalStorage` (`openDatabaseSync`, `transaction`, `executeSql`) | CREATE/INSERT/SELECT round trip; DB at `$XDG_DATA_HOME/quickshell/QML/OfflineStorage/Databases/<hash>.sqlite` (fixed path, no custom file) |
| mkdir | **AVAILABLE implicitly**: `FileView.setText()` creates missing parent directories | wrote `/tmp/lme-cap-probe/nested/deeper/file.json` from nothing, content exact |
| binary read/write, chmod, exclusive-create, stat | **STILL UNVERIFIED** (not proven absent) | FileView exposes a `data` property + `setData()` — untested for binary |

Gotchas found the same round:
- `FolderListModel` is **async and single-level**; recursion needs nested models
  or `find` through `Process`. `nameFilters:["thermal_zone*"]` with
  `showDirs:false` returns **0** — sysfs thermal_zone entries are symlinks to
  directories, so they count as dirs.
- **`/usr/bin/qml` is Qt5** on Fedora (`qt5-qtdeclarative-devel`): a Qt6 probe
  through it prints "Did not load any objects, exiting." Use `quickshell -p`.
- QML `console.log` in a probe goes to the instance log
  (`/run/user/1000/quickshell/by-id/<id>/log.log`), not reliably to stdout —
  write probe results with FileView to a file instead.
- Upstream releases: still **v0.3.2** (2026-10-08), master `9b0f339`
  (2026-10-17) — re-checked 2026-11-11 via the GitHub API.

## 1. Facts my training data gets WRONG

| Training belief | Reality (verified) | Evidence |
|---|---|---|
| "Quickshell has no Bluetooth API" | **Wrong.** `Quickshell.Bluetooth` exists since **0.2.0**: `Bluetooth` singleton (defaultAdapter, adapters, devices), `BluetoothAdapter` (enabled, discoverable, discovering, pairable + timeouts), `BluetoothDevice` (name, address, state, connected, paired, trusted, blocked, **per-device battery**, `connect()/disconnect()/pair()/cancelPair()/forget()`) | `src/bluetooth/bluez.hpp:63-76`, `adapter.hpp:57-89`, `device.hpp:55-122`; changelog `v0.2.0.md` "Bluetooth Module" |
| "Quickshell has no NetworkManager bindings" | **Wrong.** `Quickshell.Networking` since **0.3.0**: `Networking` singleton (devices model, wifiEnabled, connectivity + check), `NetworkDevice` (networks, state, nmManaged, autoconnect), `WifiNetwork` (signalStrength, security, **`connectWithPsk(psk)`**), `WifiDevice` (scannerEnabled, mode), `Network.connect()/disconnect()/forget()`, **`NMSettings.read()/write(settings)`** for saved-connection/hotspot editing | `src/network/qml.hpp:79-114`, `wifi.hpp:17-67`, `nm/settings.hpp:22-50`; changelog `v0.3.0.md` "Added network management support" |
| "File IO is manual / no atomic writes" | `Quickshell.Io.FileView` has `atomicWrites`, `watchChanges`, preload, `FileViewAdapter` + a JSON adapter class for structured data | `src/io/fileview.hpp:164-324`, `jsonadapter.hpp` |
| "No unix-socket client for IPC" | `Quickshell.Io.Socket` (Q_PROPERTY `path`, `connected`, `write()`, `flush()`, DataStream parsers) — usable for the niri IPC socket (`$NIRI_SOCKET`); also `SocketServer` with a QML handler component | `src/io/socket.hpp:20-43,95-114` |
| "Desktop entries must be parsed by hand" | `Quickshell.DesktopEntries` singleton in core: `applications` object model, `byId()`, `heuristicLookup(name)`, per-entry name/icon/comment/exec/command/categories/keywords/actions + `DesktopAction.execute()`, live monitor on file changes. **GOTCHAs (0.3.2, bit lme PR #117): the scan is ASYNC — `applications.values` is empty for >1.2 s on a real machine (poll it; no ready signal); entries expose NO OnlyShowIn/NotShowIn/TryExec, so a native list is a superset of a filtered backend list; `byId` takes the id WITHOUT the `.desktop` suffix; the scan honors XDG_DATA_HOME (a probe isolating it hides user-local apps — 11-entry false "backend-only" diff)** | `src/core/desktopentry.hpp:50-313` |
| "Battery service is read-only percentages" | `Quickshell.Services.UPower` gives `displayDevice`, `devices`, `onBattery`, per-device energy/capacity/changeRate/timeToEmpty/timeToFull/healthPercentage/isLaptopBattery/nativePath **and** `PowerProfiles` (available profiles, current, holds incl. performance degradation reasons). **GOTCHA (0.3.2, bit lme PR #115): `percentage` is normalized to a 0–1 FRACTION** — `DBusDataTransform<PowerPercentage>::fromWire` applies `wire * 0.01` (`src/services/upower/device.cpp:114-116`), unlike the raw 0–100 D-Bus property; only `Percentage` is transformed (`healthPercentage` ← D-Bus `Capacity` stays 0–100, `device.hpp:250`). Every other fraction-style QML property (Pipewire volume, wifi signalStrength, Bluetooth battery) is also 0–1 — ALWAYS multiply by 100 at the QML service boundary when the consumer contract is 0–100 | `src/services/upower/core.hpp:65-80`, `device.hpp:115-162,240-253`, `device.cpp:114-116`, `powerprofiles.hpp:107-127` |
| "The QML JS engine is basically V8 — any modern JS works" | **Wrong — it is V4 and ES2017-era.** GOTCHAs (0.3.2, bit lme PR #117 rounds 1-2): `Object.fromEntries` (ES2019) **does not exist** (runtime TypeError); ES3 future-reserved words like `native` are **rejected as QML property names** (parse error that kills the whole singleton import chain); proven FINE: `padStart`, `Object.values`, `Array.from`, arrow functions, `?.`/`??` parse. Contract-test the surface: lme `tests/test_native_files.py` bans `fromEntries` + reserved-word properties across `qml/services`; sandbox scanner `scripts/check_qml_reserved.py` | lme PR #117, real-machine rounds 2026-11-09 |
| "WifiDevice only lists networks" | `Quickshell.WifiDevice` + `WifiNetwork` (0.3.2, verified on real hardware in lme PR #118): networks model is **SSID-deduped** (per-BSSID APs merged); `Network.nmSettings` lists the saved profiles per SSID (**hotspot ap-mode profiles are skipped** — quickshell TODO, known parity gap vs nmcli); `connect()` activates the existing profile or add-and-activates; **`connectWithPsk(psk)` on a saved network UPDATES the profile's psk then activates (no duplicates)** — only valid for WpaPsk/Wpa2Psk/Sae; `Network.forget()` drops EVERY profile on the SSID — use `NMSettings.forget()` for one uuid; `scannerEnabled` false→true re-arms RequestScan (**rate-limited 10001 ms**, retry timer fires later); `Networking.wifiEnabled` is settable (radio toggle); failures surface via `Network.connectionFailed(ConnectionFailReason)` — NoSecrets/WifiClientFailed/WifiAuthTimeout/WifiNetworkLost. Real-machine parity: identical SSID sets and 0 strength deltas vs nmcli | `src/network/wifi.hpp`, `network.hpp:28-60`, `nm/wireless.cpp:88-180,255-310`, `nm/network.cpp:105-310`, `nm/settings.hpp:29-60` |
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
