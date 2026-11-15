# Kế hoạch port Lock screen riêng (ext-session-lock + PAM) — thay thế swaylock hoàn toàn

> **Agent-2, 13/11/2026.** Nguồn tham chiếu: `~/agent-collab/references/iNiR` @ edca6cc (v3.1.0), `modules/shared/lock/` — 6 file, 3.657 dòng. Mọi kết luận kỹ thuật trong văn bản này đều đã được xác minh trực tiếp: đọc code iNiR, đọc source quickshell 0.3.2 (`src/wayland/session_lock/`, `src/services/pam/`), và probe máy thật.
> **Trạng thái: Phase 0 merged (#146); Phase 1 XONG (13/11/2026, PR #147 — chờ merge).** Phase 2-4 chờ duyệt.

---

## 0. Tóm tắt cho người duyệt

Port toàn bộ cơ chế lock screen của iNiR sang shell của ta: một lock screen **của chính shell** dùng protocol Wayland `ext-session-lock-v1` (an toàn cấp compositor — niri khóa thật, không thể chụp/bypass), xác thực **PAM** (cùng cơ chế đăng nhập Fedora), **sống sót qua shell restart** (file recovery theo NIRI_SOCKET), có **nhạc + thời tiết + pin + nút nguồn** (poweroff/reboot cần mật khẩu), **mở khóa keyring tự động**, và màn hình **wallpaper blur** đúng theme của ta.

- **7-10 PR chia 5 phase** (0 → 4), mỗi phase có tiêu chí nghiệm thu trên máy thật.
- **An toàn là ràng buộc số 1**: chuỗi fallback về swaylock (còn cài sẵn) + escape hatch `loginctl unlock-sessions` + engine test không bao giờ khóa màn hình thật.
- **Phát hiện quan trọng từ probe máy**: máy này **KHÔNG có fingerprint reader** (`fprintd-list` → "No devices available") → nhánh vân tay được port đầy đủ code nhưng sẽ tự dormant (iNiR xử lý sẵn case này); việc xác thực chỉ dùng mật khẩu. Nếu sau này có máy có reader, tính năng tự bật.
- **swaylock retire theo nghĩa "shell không còn dùng"** — khuyến nghị **vẫn giữ package** làm công cụ khẩn cấp (xem mục 9, quyết định D1).

---

## 1. Hiện trạng hai bên

### 1.1. Shell ta hiện khóa màn hình bằng swaylock qua 5 đường

| # | Đường | File | Cơ chế |
|---|---|---|---|
| 1 | Phím Super+L | `config/niri/media-keys.kdl:35` | `spawn "swaylock" "--color" "22212c"` |
| 2 | Power Menu → Lock | `qml/panels/PowerMenu.qml:40` → `ShellState.run("lock")` | native router không có owner `lock` → rơi về backend → `scripts/lock_actions.py` ActionSpec → exec swaylock |
| 3 | Idle timeout (profile lock) | `qml/services/IdleState.qml` (chủ swayidle child từ Q4) → `python3 scripts/idle_control.py lock` | `secure_lock()`: swaylock `--ready-fd` + select 12s + check `/proc/<pid>/stat` birth + state file `/run/user/1000/lme-shell/session-lock.json` + guard flock |
| 4 | before-sleep (khóa trước khi ngủ) | `idle_control.py` (`idleLockBeforeSleep` preference) | cùng `secure_lock()` — handshake ready-fd trước khi logind suspend |
| 5 | Hạ tầng phụ trợ | `command_runner.py` (allowlist), `desktop_backend.py:1485`, `doctor.sh:68`, `install-fedora.sh:45`, `qml/settings/IdlePage.qml` | kiểm tra executable / cài đặt / mô tả UI |

Hạn chế: màu đặc flat `22212c` (không wallpaper), không widget (nhạc/thời tiết/pin), không poweroff/reboot từ lock, không mở keyring, shell restart làm mất giao diện khóa (swaylock vẫn khóa nhưng là chương trình ngoài).

### 1.2. iNiR: 6 file, 3.657 dòng

| File | Dòng | Vai trò |
|---|---|---|
| `Lock.qml` | 513 | Controller: `WlSessionLock` + surface mỗi màn hình, file recovery, IPC `lock.*`, fallback swaylock, heartbeat refocus, unlock keyring, targetAction (Unlock/Poweroff/Reboot), recede |
| `LockContext.qml` | 173 | Trạng thái dùng chung mọi màn hình + 2 PamContext (mật khẩu: config default `login`; vân tay: `pam/fprintd.conf` = `auth sufficient pam_fprintd.so`) + timers (PAM timeout 10s, clear 10s, finger retry 750ms) |
| `LockSurface.qml` | 2.100 | UI: 2 view clock/login, wallpaper (ảnh/gif/video) × 2 pipeline blur (FastBlur / MultiEffect-safe cho niri), overlays (gradient/smoke/unlock/dim), status row, weather, media widget, notification trên lock, power buttons, battery, input handling + focus machinery |
| `LockMediaWidget.qml` | 473 | Media player MPRIS + art + visualizer cava |
| `LockKeyboard.qml` | 303 | OSK cho cảm ứng (xkb layout) — **ta bỏ qua** (máy không cảm ứng) |
| `PasswordChars.qml` | 95 | Dấu mật khẩu hình Material shapes — optional cosmetic |

Kèm: `scripts/keyring/unlock.sh` (mở gnome-keyring bằng mật khẩu vừa nhập qua env `UNLOCK_PASSWORD`), swayidle wiring `before-sleep → 'inir' lock prepareSleep` + `after-resume → 'inir' lock focus`.

### 1.3. Cơ chế lõi của iNiR (đã đọc và xác minh từng dòng quan trọng)

1. **WlSessionLock** (Quickshell.Wayland): đặt `locked: true` → quickshell tạo `WlSessionLockSurface` cho MỖI màn hình; compositor **đảm bảo** phiên bị khóa an toàn (không chụp màn hình, khôngThoát qua Alt+F4). Nếu shell chết khi đang khóa: per ext-session-lock spec, niri **giữ khóa phiên** và hiển thị lock fallback của compositor → đây chính là lý do có file recovery.
2. **Sống sót qua shell restart**: file `$XDG_RUNTIME_DIR/inir-session-lock.state` chứa `locked|unlocked\n<NIRI_SOCKET>\n`. Shell mới khởi động → đọc file → nếu `locked` VÀ socket khớp compositor hiện tại → tự set `screenLocked = true` ngay (lock surface vẽ lại tức thì). Nếu niri restart (socket khác) → không khóa (đúng: phiên mới).
3. **Chuỗi fallback an toàn**: surface load lỗi (Loader.Error) HOẶC không load xong sau 2s → thả lock QS → exec swaylock/hyprlock. **Ta có lợi thế: giữ nguyên `idle_control.py lock` làm fallback — code sẵn có, đã test.**
4. **PAM kép**: PamContext mật khẩu (config default = `login` — dùng đúng stack Fedora: authselect/system-auth, tương thích sssd/ldap/fido2 nếu sau này cấu hình) + PamContext vân tay riêng (config `pam/fprintd.conf`, start() ngay khi khóa màn hình, retry 750ms khi quét lỗi, abort khi gõ mật khẩu). Phát hiện có vân tay: `fprintd-list $(whoami)` và regex các dòng `- #N:` (machine-readable, không phụ thuộc ngôn ngữ).
5. **Focus machinery** (bài học niri): niri đôi khi rơi focus trên ext-session-lock surface sau suspend/resume → heartbeat Timer 2s gọi refocus khi đang khóa + refocus ngay khi topology màn hình đổi + focusEnsureTimer 100ms×30 lần lúc mới khóa. Mọi focus đều qua `Qt.callLater`.
6. **Handshake suspend**: `lock prepareSleep` set khóa NGAY (bỏ qua debounce 150ms) rồi trả về `secure` (compositor đã xác nhận) hoặc `locking`; swayidle chờ `secure` trước khi thả logind inhibitor. `lock focus` sau resume.
7. **Trải nghiệm**: phím bất kỳ từ view clock → view login + capture ký tự đó; Esc xóa text / về clock; Enter/submit → tryUnlock (giữ Ctrl = "mở khóa + giữ thức" — alsoInhibitIdle); sai mật khẩu → shake animation + placeholder đỏ "Incorrect password"; timeout 10s nếu PAM treo; password tự clear sau 10s không gõ.

---

## 2. Xác minh tính khả thi (đã làm, không giả định)

| Kiểm tra | Kết quả |
|---|---|
| quickshell 0.3.2 có `WlSessionLock`/`WlSessionLockSurface`? | ✅ `src/wayland/session_lock/` (lock/surface/manager, QML_ELEMENT). Docs cảnh báo đúng semantics: chỉ 1 lock active; shell exit khi locked → compositor giữ khóa |
| `Quickshell.Services.Pam`? | ✅ `src/services/pam/`: PamContext (config default **"login"**, configDirectory **tuyệt đối**, user, message, responseRequired, `start()/abort()/respond()`), PamResult (Success/Failed/Error/MaxTries), abort qua subprocess riêng — đúng cách iNiR dùng |
| niri hỗ trợ ext-session-lock? | ✅ niri 26.04 trên máy (có từ 0.1) |
| Máy thật | ✅ Quickshell 0.3.2 (COPR), config deployed `~/.config/quickshell/lme-shell` @ b3deed1 = main |
| Fingerprint | ⚠️ fprintd 1.94.5 cài nhưng **"No devices available"** — không có reader → nhánh finger dormant (graceful sẵn trong code iNiR) |
| Keyring | ✅ gnome-keyring-daemon có → port tính năng unlock keyring |
| Môi trường shell | ✅ `NIRI_SOCKET=/run/user/1000/niri.wayland-1.3135.sock`, `XDG_RUNTIME_DIR=/run/user/1000`, `WAYLAND_DISPLAY=wayland-1` trong env tiến trình shell → file recovery hoạt động |
| Pin laptop | ✅ BAT1 + ACAD → widget pin trên lock screen có ý nghĩa |
| Blur | iNiR dùng **MultiEffect client-side** cho niri ("safe pipeline" — FastBlur shader có thể leak red buffer trên một số GPU). Lưu ý: ext-session-lock surface KHÔNG phải layer-shell → niri `layer-rule`/background-effect KHÔNG áp dụng được cho lock surface → blur client-side là đường đúng (quyết định D2) |

---

## 3. Thiết kế đích — mapping file

Nguyên tắc: giữ pattern iNiR, đổi điểm neo về kiến trúc ta (ShellState/native router/Theme/prefs), tách file theo cap 250 dòng của check-architecture, REL/INVARIANT/GOTCHA headers, đăng ký WORKSPACE_MAP + architecture.json (owner mới: `lock`).

### 3.1. File mới (8 file QML + 2 config/script)

| File mới (của ta) | ~Dòng | Port từ iNiR | Ghi chú thiết kế |
|---|---|---|---|
| `qml/services/LockState.qml` | 240 | `Lock.qml` (513) | Singleton trong `qml/services/qmldir`. Sở hữu `WlSessionLock`, file recovery `$XDG_RUNTIME_DIR/lme-shell/session-lock-v2.state` (không đè file cũ của idle_control), IpcHandler target **`lock`** (activate/prepareSleep/deactivate/status/focus — cùng surface IPC như iNiR), debounce 150ms, fallback → `idle_control.py lock`, heartbeat refocus 2s, unlock keyring, targetAction, launchOnStartup. Env gate `LME_SHELL_LOCK_ENABLED=0` để engine test vô hiệu hóa lock thật |
| `qml/lock/LockContext.qml` | 170 | `LockContext.qml` (173) | Non-singleton, LockState instantiate. 2 PamContext (mật khẩu default `login`; finger `configDirectory: Quickshell.shellPath("config/pam")`, config `fprintd.conf`), các timer 10s/10s/750ms, fprintd-list detection |
| `qml/lock/LockSurface.qml` | 250 | `LockSurface.qml` (2.100) | Root MouseArea + state clock/login + INPUT HANDLING (any-key→login+capture, Esc, Enter, ctrlHeld, focus machinery) + thuần chủ root |
| `qml/lock/LockWallpaper.qml` | 130 | phần wallpaper | Chỉ ảnh tĩnh (shell ta không có wallpaper gif/video) từ `WallpaperState` hiện tại + MultiEffect blur (D2) + zoom 1.1 + gradient + dim overlay. `cache: false` (bài học QPixmapCache leak #163/#164 của iNiR) |
| `qml/lock/LockClockView.qml` | 240 | view clock | Đồng hồ lớn + status row (wifi/bt/volume) + weather (WeatherState Q5 native) + pin (PowerState) + hint text. Dùng Theme/ThemeCurve của ta, không Appearance |
| `qml/lock/LockLoginView.qml` | 230 | view login | Card mật khẩu (glass component của ta) + TextInput + shake khi sai + indicator đang xác thực + fingerprint hint (dormant) + power buttons (suspend/poweroff/reboot — 2 cái sau cần mật khẩu vì `requirePasswordToPower`) |
| `qml/lock/LockMediaWidget.qml` | 200 | `LockMediaWidget.qml` (473) | Tái dùng MPRIS pattern từ ActivityState/MediaActions + art qua cache ảnh hiện có; bỏ cava visualizer (giảm phức tạp, có thể thêm sau) |
| `config/pam/fprintd.conf` | 1 | y nguyên `auth sufficient pam_fprintd.so` | Dormant trên máy này |
| `scripts/keyring_unlock.sh` | 30 | `scripts/keyring/unlock.sh` | python/bash, nhận `UNLOCK_PASSWORD` env, gọi gnome-keyring-daemon --login; chạy qua CommandRunner allowlist |
| `tests/cases/lock/…` | — | — | Engine cases (mục 7) |

Password dots: dùng chấm tròn Theme đơn giản trong LockLoginView (PasswordChars shapes = cosmetic, defer).

### 3.2. File sửa (7 file)

| File | Thay đổi |
|---|---|
| `config/niri/media-keys.kdl` | Super+L → `spawn "quickshell" "-c" "lme-shell" "ipc" "call" "lock" "activate"` |
| `qml/services/IdleState.qml` | `idleCommand()`: timeout-lock và before-sleep → `quickshell -c lme-shell ipc call lock prepareSleep`; after-resume → `lock focus` + giữ `power-on-monitors`; `requiredNames` bỏ swaylock khỏi bắt buộc (chuyển thành optional-fallback) |
| `scripts/idle_control.py` | `secure_lock()` GIỮ NGUYÊN (thành fallback của LockState + công cụ khẩn cấp); `sleep --lock` đổi handshake: gọi `quickshell ... ipc call lock prepareSleep`, nếu trả `locking` thì poll `lock status` tới `secure` (timeout 12s) → exit 0; nếu IPC fail → fallback về secure_lock() swaylock |
| `qml/panels/PowerMenu.qml` | Không đổi logic (vẫn `ShellState.run("lock")`); thêm `LockState.handles("lock")` vào `ShellState.nativeOwner()` — action lock thành native owner (đúng pattern Q4-Q6), `lock_actions.py` giữ làm cửa sổ A/B rồi retire ở Phase 4 |
| `qml/settings/` | Trang LockPage mới (launchOnStartup, keyring unlock on/off, blur on/off, animations on/off) + IdlePage đổi mô tả "Wait for swaylock..." → "Wait for the session lock..." |
| `scripts/doctor.sh` + `install-fedora.sh` | swaylock: required → optional note "emergency fallback"; dnf install giữ ở Phase 4 theo D1 |
| `THIRD_PARTY.md` + `third_party/` | Thêm mục lock module (iNiR @ edca6cc); copy NOTICE nếu chưa |

### 3.3. Tích hợp các service sẵn có của ta

- **Wallpaper**: `WallpaperState` (đường dẫn hiện tại) → LockWallpaper.
- **Thời tiết**: `WeatherState` (Q5 native) → LockClockView.
- **Pin**: `PowerState`/`PeripheralBatteries` → LockClockView (BAT1).
- **Media**: pattern MPRIS từ `ActivityState`/`MediaActions` → LockMediaWidget.
- **Idle**: `IdleState` (chủ swayidle) — rewiring ở 3.2.
- **Prefs**: qua `prefs_store.py`/StorageState single-writer (Q6) — lock preferences là preference keys mới, schema cập nhật.
- **Auth UI pattern**: AuthenticationAgent (Polkit) đã có pattern hộp thoại mật khẩu + IpcHandler — tái dùng kinh nghiệm.

---

## 4. An toàn lock screen (ràng buộc số 1 — đọc trước khi duyệt)

1. **Không bao giờ khóa mình khỏi máy khi test**: mọi engine case chạy với `LME_SHELL_LOCK_ENABLED=0` → LockState vô hiệu (không tạo WlSessionLock, IPC trả "disabled"); test PAM headless dùng config `pam_permit`/mật-khẩu-sai không cần wayland.
2. **Live protocol (chạy trên máy thật qua opencode) luôn có 2 escape hatch mở sẵn trước khi khóa**: (a) một terminal khác chạy sẵn lệnh `loginctl unlock-sessions` (chỉ cần Enter); (b) khả năng `quickshell -c lme-shell ipc call lock deactivate`. Ghi rõ trong checklist từng buổi test.
3. **Chuỗi fallback 3 tầng**: surface lỗi/hang 2s → swaylock qua `idle_control.py lock` (còn cài); swaylock thiếu → notify critical "Lock failed". LockState detect qua Loader.Error + fallbackTimer (port nguyên).
4. **PAM timeout 10s** + password clear 10s (port nguyên) — không treo UI vĩnh viễn.
5. **File recovery chỉ tin khi socket khớp** (port nguyên) — shell restart giữ khóa, niri restart không khóa lại phiên mới.
6. **Hot reload khi đang khóa bị vô hiệu** (port: nếu `locked`, từ chối reload — start.sh kiểm tra `lock status` trước khi kill shell cũ).
7. **prepareSleep phải chờ `secure`** trước khi thả inhibitor (port + poll) — không bao giờ ngủ với màn hình chưa khóa.
8. **Quy tắc AGENTS.md áp dụng đầy đủ**: test-first, revert-don't-fix-forward, xác thực máy thật trước khi tuyên bố xong; engine case phải lái seam ngoài cùng (LESSON 81: test WlSessionLock wiring, không chỉ test hàm logic).

---

## 5. Phases & PRs

### Phase 0 — Nền tảng kiểm chứng (1 PR, không đổi hành vi)
- Vendored `config/pam/fprintd.conf` + `scripts/keyring_unlock.sh` (chưa gọi).
- Engine cases: PamContext với config test (`pam_permit.so` → Success; `pam_unix` mật khẩu sai → Failed + showFailure) — chứng minh PAM chạy headless trên máy; LockState skeleton với env gate (load được, inert).
- **Nghiệm thu**: G0 xanh; engine case PAM pass trên máy thật (spawn quickshell thật, không lock màn hình).

### Phase 1 — Lock core (2-3 PR)
- PR1: `LockState` + `LockContext` + IPC `lock.*` + file recovery + fallback chain + native router `handles("lock")` + engine cases (state machine, recovery logic, IPC surface).
- PR2: `LockSurface` + `LockWallpaper` (blur theo D2) + `LockLoginView` (mật khẩu, shake, power buttons) + keybind flip media-keys.kdl + focus machinery.
- **Nghiệm thu (live protocol L1)**: Super+L khóa; gõ sai → shake; đúng → mở + keyring mở (`secret-tool lookup` có kết quả); `lock status` đúng 4 trạng thái; restart shell khi khóa → vẫn khóa, unlock được; fallback: giết surface bằng cách trỏ keybind tới file hỏng → swaylock xuất hiện; escape hatch demo.

### Phase 2 — Idle & suspend integration (1-2 PR)
- IdleState rewiring (timeout lock / before-sleep prepareSleep / after-resume focus) + idle_control `sleep --lock` poll handshake + bỏ swaylock khỏi required.
- **Nghiệm thu (live L2)**: idle timeout khóa đúng; suspend thủ công: before-sleep log ra `secure` trước khi ngủ; resume → focus về lock, gõ mật khẩu mở được (đây là chỗ niri hay rơi focus — heartbeat phải cứu được); `idleLockBeforeSleep=false` vẫn hoạt động.

### Phase 3 — Trải nghiệm đầy đủ (2-3 PR)
- `LockClockView` (đồng hồ + weather + pin + status row) + `LockMediaWidget` + animations (Theme curves, view transitions, recede 250ms) + LockPage settings + doctor.sh + IdlePage rewording + unlock overlay.
- **Nghiệm thu (live L3)**: khóa thấy đồng hồ/thời tiết/pin; phát nhạc → media widget hiện, điều khiển được từ lock; đổi prefs có hiệu lực; battery saver tắt blur đúng chính sách.

### Phase 4 — Retire swaylock (1 PR, sau ≥1 tuần ổn định + duyệt D1)
- `lock_actions.py` đánh dấu superseded (native owner chốt); command_runner allowlist dọn; install-fedora.sh swaylock → optional; docs (README, MIGRATION_LOG, WORKSPACE_MAP, ARCHITECTURE) cập nhật; THIRD_PARTY mục lock.
- **Khuyến nghị**: GIỮ swaylock cài đặt làm công cụ khẩn cấp (D1) — shell không còn gọi nó ngoài fallback.

Tổng: **7-10 PR**. Mỗi PR: engine case kèm theo + xác thực máy thật qua opencode + journal entry.

---

## 6. Kiểm thử chi tiết

**Engine cases (G0, headless, `LME_SHELL_LOCK_ENABLED=0`):**
1. PamContext permit/unix-sai (seam thật: PamContext subprocess).
2. LockState state machine: activate (debounce) → locked; deactivate; status 4 trạng thái; prepareSleep bỏ debounce + trả locking/secure (mock lock.secure).
3. Recovery: viết file `locked\n<socket hiện tại>` → khởi động LockState → locked=true; socket khác → unlocked.
4. Fallback: surface Loader.Error → gọi helper lock (assert argv) — seam: Process command.
5. IdleState.idleCommand argv mới (before-sleep = ipc prepareSleep, sau resume = focus) — seam: hàm sinh argv (pure).
6. idle_control sleep --lock: IPC trả "locking" rồi "secure" (mock qs binary trong PATH fixture) → exit 0.

**Live protocols L1-L3**: mục 5; mỗi buổi test qua opencode có: 2 escape hatch mở sẵn, log `journalctl --user -u <shell>` theo dõi, quay video màn hình nếu cần, và chạy vào buổi (không cuối tuần).

---

## 7. Rủi ro & mitigation

| Rủi ro | Mức | Mitigation |
|---|---|---|
| Kẹt ngoài màn hình (lock hỏng) | Cao nếu làm ẩu | Mục 4 toàn bộ; fallback 3 tầng; escape hatches; live test ban ngày |
| niri rơi focus sau resume | Trung bình (iNiR đã gặp) | Heartbeat 2s + refocus on screens-changed + focusEnsureTimer — port nguyên, verify ở L2 |
| PAM config default `login` hành xử khác Fedora thường | Thấp | Phase 0 test trực tiếp; nếu cần, ship config pam riêng (configDirectory tuyệt đối) |
| MultiEffect blur nặng trên iGPU | Trung bình | Đo ở L1 (fps/CPU); fallback "dim-only" mode; tắt khi battery saver |
| 250-line cap | Chắc chắn gặp | Đã tách 7 file từ thiết kế (mục 3.1) |
| Swayidle child chết khi shell restart đang khóa | Thấp | Trước-sleep inhibition do logind giữ; recovery file khôi phục lock; IdleState tự start lại |
| Reload QML khi đang khóa | Trung bình | Vô hiệu reload khi locked (port iNiR); start.sh kiểm tra status |
| GPL-3.0 attribution | Thấp | Header snowarch/GPL-3.0 ở các file dẫn xuất rõ; THIRD_PARTY ghi edca6cc; third_party/iNiR-NOTICE |

---

## 8. Pháp lý

Lock module iNiR là GPL-3.0 (fork illogical-impulse). Repo ta AGPL-3.0-or-later — tương thích theo §13 GPL-3.0. Các file port gần nguyên trạng (LockContext, cơ chế recovery, focus patterns): giữ header bản quyền snowarch + ghi nguồn edca6cc. Pattern viết lại theo kiến trúc ta (LockState, các view): ghi công tham khảo trong THIRD_PARTY.md.

---

## 9. Quyết định cần chủ sở hữu duyệt (D1-D6)

| # | Quyết định | Khuyến nghị của Agent-2 |
|---|---|---|
| D1 | Swaylock: gỡ package hay giữ làm fallback khẩn cấp? | **Giữ package** (shell không còn dùng nó thường xuyên; `idle_control.py lock` vẫn là tầng fallback + công cụ khẩn cấp terminal) |
| D2 | Blur nền lock: MultiEffect client-side (như iNiR) hay chỉ dim? | **MultiEffect** + tắt khi battery saver; có toggle trong LockPage |
| D3 | Mở keyring tự động sau khi unlock? | **Có** (máy có gnome-keyring; opt-out trong LockPage) |
| D4 | Media widget + thời tiết + pin trên lock screen (Phase 3)? | **Có** — đây là phần "đáng giá" nhất so với swaylock |
| D5 | Preference "khóa khi shell khởi động" (launchOnStartup)? | **Có** (port, mặc định tắt) |
| D6 | Duyệt trọn 5 phase hay từng phase một? | **Trọn kế hoạch, nghiệm thu từng phase** (nhanh hơn nhưng vẫn an toàn vì mỗi phase có gate máy thật) |

---

## 10. Thứ tự triển khai sau duyệt

1. Agent-2 tạo subagent session qua opencode (mỗi phase 1 session, model mạnh cho Phase 1) + branch `feat/native-lock-screen`.
2. Phase 0 ngay sau duyệt (kết quả PAM xác nhận con đường); Phase 1 song song nghiên cứu chi tiết UI theme.
3. Mỗi PR: engine case → sandbox G0 → máy thật (L1/L2/L3) → journal → steer Agent-1 → merge.
4. Sau Phase 4: cập nhật báo cáo so sánh iNiR (Tier B4 → DONE) + OPTIMIZATION_PLAN ghi nhận độ trễ khởi động thêm.

*File này là nguồn sự thật cho việc triển khai. Mọi thay đổi thiết kế trong lúc port phải cập nhật ngược lại đây + journal.*
