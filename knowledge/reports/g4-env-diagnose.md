# A4c C2 — G4 environment diagnose + LME_TEST_POINTER

- **Ngày:** 2026-11-15 (giờ máy, Asia/Ho_Chi_Minh)
- **Repo:** `~/lme-fedora-niri-qs` @ `753dbc6` (main sau PR #167), working tree sạch
- **Shell live:** PID `1315627`, IPC `lock status=unlocked`
- **Phạm vi:** ops-only. Không sửa code repo, không sửa test, không mở PR trong chặng này.
- **Kết luận ngắn:** G4 **chưa xanh**: 35 test → **24 pass / 11 fail / 0 skip**, ổn định qua 2 lần chạy. Cả 11 failure đã được gọi tên + có bằng chứng tái lập. Trong đó **2 bug sản phẩm thật** (đề xuất PR riêng), **6 failure do test/fixture cũ sau Q5**, **2 failure do race tín hiệu readiness trong test**, **1 failure do giới hạn tooling `Canvas.save()`** của Quickshell 0.3.2. Recipe môi trường + pointer dir đã đóng gói, tái sử dụng được cho G1–G3.

---

## 1. Inventory `LME_TEST_*` và helper

### 1.1 Gate flags (4 module G4)

| Flag | Module / case | Ý nghĩa |
|---|---|---|
| `LME_TEST_CLIPBOARD_NATIVE=1` | `test_clipboard.NativeClipboardCase` | watcher/supervisor + clipboard CLI thật trên Wayland riêng |
| `LME_TEST_CLIPBOARD_UI=1` | `test_clipboard.ClipboardInterfaceCase`, `test_clipboard_entry.NativeEntryCase`, `test_clipboard_withdrawal.NativeWithdrawalCase` | shell/settings thật + pointer thật |
| `LME_TEST_ANNOTATION_UI=1` | `test_image_annotation_ui.AnnotationInterfaceCase` | notification → annotation qua D-Bus riêng |
| `LME_TEST_CAPTURE_UI=1` | `test_capture_night.NativeCaptureCase` | screenshot editor fixture + OCR thật |

### 1.2 Pointer env

| Env | Helper | Gọi từ |
|---|---|---|
| `LME_TEST_POINTER` | `pointer-click x y` | `test_capture_night.py:323`, `clipboard_slice_fixture.py:164`, test annotation/clipboard UI |
| `LME_TEST_POINTER_RIGHT` | `pointer-right x y` | `test_clipboard.py` (preview ảnh), fixture |
| `LME_TEST_DRAG` | `pointer-drag x1 y1 x2 y2` | `test_capture_night.py` (vẽ annotation) |
| `pointer-move x y ms` | có sẵn trong `~/glm-work/lme-pointer/` | `test_personalization.py:219` (ngoài G4) |

`tests/migration_checks.py` giữ đúng 3 env `POINTER` / `DRAG` / `POINTER_RIGHT` khi lọc env, nên không cần export thêm biến khác cho G4.

---

## 2. Dependency inventory

Có mặt: `sway 1.11`, `swaymsg`, `dbus-run-session`, `quickshell 0.3.2` (Fedora COPR), `python3 3.14.10`, `qmllint`, `grim`, `slurp`, `wl-copy`, `wl-paste`, `swappy`, `wf-recorder`, `pactl`, `wtype`, `busctl`, `tesseract`, `jq`, `notify-send`.
Thiếu: **`satty`** — không chặn G4 vì các test annotation/capture đều cấy binary giả vào `PATH`; nhưng live shell đặt `captureEditor=satty` sẽ không annotate được nếu máy thật thiếu satty.

Hệ điều hành: Fedora Linux 44, kernel `7.2.15-200.fc44.x86_64`.

---

## 3. Pointer helpers và verify

Location: `~/glm-work/lme-pointer/`

- `lme-pointer` — ELF helper (Wayland virtual pointer), subcommand `click|right|drag|move`.
- Wrapper: `pointer-click`, `pointer-right`, `pointer-drag`, `pointer-move` — chỉ `exec lme-pointer <kind> "$@"`.
- `env.sh` — export 4 gate flags.
- `verify.sh` + `verify-pointer.qml` — dựng headless Sway + QML counter thật, bấm/phải/kéo rồi so count.

Kết quả verify (đã chạy lại trong C2):

```
pointer helpers OK: {'clicks': 1, 'rights': 1, 'drags': 1}
```

Đây là bằng chứng helpers thao tác được trên Wayland thật, không chỉ “có file”.

---

## 4. Recipe tái sử dụng cho G1–G3

### 4.1 Chạy gate chính thức

```bash
cd ~/lme-fedora-niri-qs
./scripts/run-gates.sh \
  --output /tmp/opencode/a4c-g4-run2 \
  --env-file ~/glm-work/lme-pointer/env.sh \
  --pointer-dir ~/glm-work/lme-pointer \
  --gates G4
```

`run-gates.sh` tự dựng XDG/Sway/D-Bus disposable; không cần đăng nhập session thật. Kết quả ghi `G4.log` + `summary.json`.

### 4.2 Runner rút gọn để tái hiện 1 test

`~/glm-work/lme-pointer/run-in-g4-env.sh <output-dir> <command...>` — private D-Bus + headless Sway + XDG sandbox + đủ 4 flag/pointer env, dùng lại được cho G1–G3:

```bash
~/glm-work/lme-pointer/run-in-g4-env.sh /tmp/opencode/a4c-diag/case \
  python3 -m unittest -v test_capture_night.NativeCaptureCase
```

Lưu ý: script dùng `LME_GATE_REPO` (mặc định `~/lme-fedora-niri-qs`) và `cd` vào repo trước khi chạy.

---

## 5. Hai lần chạy G4

| Run | Tests | Pass | Fail | Skip | Wall | Evidence |
|---|---:|---:|---:|---:|---:|---|
| 1 | 35 | 24 | 11 | 0 | 72.428s | `/tmp/opencode/a4c-g4/` |
| 2 | 35 | 24 | 11 | 0 | 72.134s | `/tmp/opencode/a4c-g4-run2/` |

Hai lần cho **cùng một tập failure**, cùng thứ tự — không phải flake ngẫu nhiên. Không có skip ẩn; mọi test đều chạy thật.

> Baseline trước C2 là G4 21/5/8 vì các leg native/UI bị skip. Bật đủ 4 flag làm lộ fixture cũ và race môi trường, đúng mục tiêu của C2.

---

## 6. Phân loại 11 failure

| # | Test | Triệu chứng | Nguyên nhân | Nhóm |
|---:|---|---|---|---|
| 1 | `test_image_annotation_ui...live_screenshot_toast...` | `busctl Notify` rc 1: name chưa có owner | test gọi Notify trước khi `org.freedesktop.Notifications` đăng ký (service xuất hiện 1.47s; test gọi 1.14s). Predicate `idleStatus` không chờ backend | Test race |
| 2 | `test_clipboard.NativeClipboardCase.test_the_watcher_dies...` | watcher vẫn sống sau khi kill “parent” | test kill `sleep` không phải kernel-parent của watcher; `--parent $$` là PID `sh` wrapper đang `wait` | Test sai thiết kế |
| 3 | `test_clipboard.ClipboardInterfaceCase.test_search_and_keyboard_copy...` | `ReferenceError: previewClose is not defined` | bug thật: A1 (`c8d0cfd`) xoá `id: previewClose` nhưng còn 1 call ở `ClipboardPanel.qml:127` | **Bug sản phẩm** |
| 4 | `test_capture_night.NativeCaptureCase.test_drawing...` | `Editor state timeout` | fixture `capture-demo.qml` dựa vào `Canvas.save()`; build Quickshell/Qt này trả `false` + `QFSFileEngine::open: No file name specified`, nên `sourceReady` không bao giờ true | Tooling/environment |
| 5 | `test_capture_night...test_shell_capture...` | `Shell capture timeout` tại `wait(windows)` | test chờ `idleStatus` (luôn truthy) rồi bắn `capture`; `ShellState.send()` drop request khi `backendReady=false`. Capture đầu bị mất | Test race |
| 6 | `test_clipboard_entry...test_bar_ipc...` | `9 != 1` | fixture đếm **mọi** lần gọi `clipboard.py` là “worker”; Q5 đã bỏ serve daemon, one-shot `--state/--search` làm bẩn marker | Fixture cũ sau Q5 |
| 7 | `test_clipboard_entry...test_demo_preview...` (demo) | `['pid'] != []` | fixture cũ + bug thật: demo mở panel vẫn gọi `clipboard.py --state` do thiếu demo guard | Fixture + **bug sản phẩm** |
| 8 | `test_clipboard_entry...test_demo_preview...` (preview) | `['pid','pid'] != []` | như trên | Fixture + **bug sản phẩm** |
| 9 | `test_clipboard_entry...test_image_click...` | `No visible control: clipboardImage0` | wrapper fixture `os.execv(..., [python, actual])` **nuốt toàn bộ argv**, nên `--search` biến thành no-op; entries luôn 0 | Fixture cũ sau Q5 |
| 10 | `test_clipboard_entry...test_preview_initial...` | `['pid'] != []` | như #7/#8 | Fixture + **bug sản phẩm** |
| 11 | `test_clipboard_withdrawal...test_disable_preserves...` | `3 != 1` | như #6 | Fixture cũ sau Q5 |

Không có failure nào do thiếu tool thật. `satty` thiếu nhưng mọi test liên quan đều mock.

---

## 7. Chi tiết nguyên nhân

### 7.1 Bug thật #1 — `previewClose` (A1 regression)

`qml/panels/ClipboardPanel.qml:127`:

```qml
MouseArea { objectName: "clipboardImage" + entry.index; ... onClicked: mouse => {
  if (mouse.button === Qt.RightButton) {
      root.previewImage = entry.modelData.image;
      previewClose.forceActiveFocus();   // <-- không còn tồn tại
  } else ShellState.run("imageAnnotate", ...);
} }
```

- `git log -S'previewClose'` → A1 commit `c8d0cfd` xoá `id: previewClose` cùng toàn bộ clear-confirmation UI nhưng bỏ sót call này.
- Hệ quả: right-click ảnh mở preview nhưng ném ReferenceError; focus bàn phím không vào preview, `Esc`/keyboard không đúng.
- Test bắt được vì scan log cuối test (`ReferenceError`).
- Đề xuất: PR riêng, thay bằng `root.focusSearch()` hoặc focus item preview còn tồn tại. Không sửa trong C2.

### 7.2 Bug thật #2 — demo/preview gọi tool ngoài ý muốn

`qml/services/ClipboardState.qml:173`:

```qml
onMonitoringChanged: if (monitoring && ready) refreshState()
```

- Thiếu guard `!ShellState.demo` (và nên có `!ShellState.settingsApp`), trong khi debounce ngay dưới đã có guard đó (dòng 171).
- Trong demo `ready = ShellState.demo` (dòng 21), nên mở panel → `refreshState()` → chạy `clipboard.py --state` thật.
- Bằng chứng probe: `started:false` nhưng argv ghi được `["--directory", ".../clipboard", "--state"]`.
- Đề xuất: PR riêng (cùng PR với `previewClose` nếu owner muốn gom clipboard fixes). Không sửa trong C2.

### 7.3 Fixture clipboard cũ sau Q5 (6 failure)

`tests/clipboard_slice_fixture.py` vẫn giả định mô hình **serve daemon**:

1. **Đếm worker:** wrapper ghi PID mỗi lần `scripts/clipboard.py` chạy. Sau Q5, mỗi `--state/--search/--copy/...` là một process one-shot → marker phình lên (9, 3, 1–2 dòng). Thực tế không còn daemon; watcher là `clipboard_watch.py` → `wl-paste`.
2. **Nuốt argv:** wrapper dùng
   ```python
   os.execv(sys.executable, [sys.executable, str(actual)])
   ```
   không truyền `sys.argv[1:]`. Vì vậy mọi `--search` thành “no action”, trả `{ok,total,revision}` không có `entries`; `ClipboardState.entries` luôn rỗng → `clipboardImage0` không tồn tại. Đây chính là failure #9.
3. **Kỳ vọng “1 worker”** là kỳ vọng của serve daemon cũ, không còn đúng: khi `clipboardEnabled=false` thì không có watcher nào; khi bật text-only thì có 1 `clipboard_watch.py`.

Bằng chứng bổ sung (fix trong bộ nhớ, không sửa repo):
- Forward `argv` + chỉ log watcher: `test_image_click`, `test_demo_preview...`, `test_preview_initial...` **PASS**.
- Hai test worker-count vẫn `0 != 1` vì chúng cần đếm process `clipboard_watch.py`/`wl-paste`, không phải wrapper `clipboard.py` → xác nhận cần **sửa contract test**, không chỉ một dòng fixture.
- Log: `/tmp/opencode/a4c-diag/fixture-proof2.log`.

Kết luận: 6 failure thuộc nhóm “test contract/fixture tiền Q5”; sửa cần owner duyệt vì tests là gitignored và không được tự ý sửa assertion.

### 7.4 Race readiness trong test (2 failure)

Cả hai test dùng:

```python
json.loads(ipc('idleStatus')).get('source')
```

như tín hiệu “shell đã sẵn sàng”. Nhưng `idleStatus` trả `ShellState.idle` = `IdleState.section`, mà section mặc định đã có `source: "ac"`. Vì vậy predicate truthy **ngay từ frame đầu**, trước khi `backendReady` và trước khi notification server đăng ký.

- **Annotation:** `Notify` gọi ở 1.14s; `org.freedesktop.Notifications` xuất hiện ở 1.47s → `name ... not provided by any .service files`.
- **Shell capture:** `ipc('capture','screen')` → `takeScreenshot` hẹn 250ms → `root.run('screenshot')`; `send()` thấy `!backendReady` nên drop, chỉ set status message. Test chờ cửa sổ 10s → timeout.
- Bằng chứng:
  - Capture ngay sau `idleStatus`: không có cửa sổ sau 6s; retry sau 2s → cửa sổ xuất hiện sau 1.2s (`shell-probe4-retry.log`).
  - Chờ 3s trước capture → cửa sổ xuất hiện sau 1.1s (`shell-probe3-delay.log`).
  - Vì sao trước đây “pass một mình”: backend kịp ready trong cửa sổ 250ms; test nặng chạy trước làm chậm → race thành deterministic.

Đề xuất test fix (cần owner duyệt): chờ tín hiệu thật (`FeatureCatalog.settled && backendReady`, hoặc bus name owner cho notification), không dùng `idleStatus`.

### 7.5 Watcher PDEATHSIG test sai

Test tạo `self.parent = Popen(['sleep','60'])`, rồi chạy watcher bằng `sh -c 'python3 clipboard_watch.py --parent $$ ... & wait'`. Trong `sh -c`, `$$` là PID của `sh`, không phải `sleep`. Kernel parent của watcher cũng là `sh` (đang `wait`). Vì vậy:

- `--parent` trỏ đúng `sh` (còn sống) → PDEATHSIG không bắn.
- `self.parent.kill()` giết `sleep` — process không liên quan.
- Watcher sống là **đúng thiết kế**; test sai. Muốn test PDEATHSIG phải cho watcher làm con trực tiếp của process bị kill.

### 7.6 `Canvas.save()` không hoạt động trong build này

Fixture `capture-demo.qml` ghi ảnh nguồn bằng:

```qml
if (!root.sourceReady && root.session.path && save(root.session.path)) root.sourceReady = true;
```

Probe cô lập (Canvas.Image, absolute path và `file://` URL, cả default target) đều trả `save=false`, kèm:

```
QFSFileEngine::open: No file name specified
```

→ `sourceReady` không bao giờ true → `ScreenshotEditor` không mount → `state.ready=false` → `Editor state timeout`. Đây là giới hạn tooling/quickshell 0.3.2 + Qt build, không phải logic sản phẩm. Hướng xử lý (owner quyết): thay fixture bằng ảnh PNG dựng sẵn (Python/grim) thay vì `Canvas.save()`, hoặc chấp nhận skip có ghi tên tooling.

---

## 8. Đánh giá tiêu chí đóng C2

- G4 **không xanh**: 24/35.
- **0 skip**, nên không có “skip ẩn vì thiếu tool”.
- **11/11 failure đã gọi tên** + có log/probe tái lập; không còn failure “chưa hiểu nguyên nhân”.
- Recipe môi trường + pointer dir tái sử dụng được cho G1–G3 (mục 4).

Theo §9 bước 5, C2 có thể đóng ở trạng thái “diagnose complete, G4 đỏ đã phân loại đầy đủ”, với các quyết định cần owner:

1. **Duyệt sửa test/fixture cục bộ** (gitignored): post-Q5 clipboard contract (#6,#7,#8,#9,#10,#11), readiness signal (#1,#5), watcher PDEATHSIG (#2). Dự kiến sau sửa: 9 failure biến mất; còn 2 bug thật + 1 tooling.
2. **Duyệt PR riêng** cho `previewClose` (#3) và demo guard (#7/#8/#10) — không trộn vào chặng ops.
3. **Quyết định cho drawing fixture** (#4): workaround fixture hay ghi nhận environment gap.
4. `satty` thiếu trên máy: chỉ ảnh hưởng live annotation, không chặn G4.

Sau khi owner chốt, C3 (L2 live test) mới có ý nghĩa chạy tiếp vì cần owner có mặt cho idle/suspend/resume/password.

---

## 9. Phụ lục tái lập

| Việc | Lệnh / file |
|---|---|
| G4 đầy đủ | `./scripts/run-gates.sh --output /tmp/opencode/a4c-g4-run2 --env-file ~/glm-work/lme-pointer/env.sh --pointer-dir ~/glm-work/lme-pointer --gates G4` |
| 1 test trong G4 env | `~/glm-work/lme-pointer/run-in-g4-env.sh <out> python3 -m unittest -v <case>` |
| Pointer verify | `~/glm-work/lme-pointer/verify.sh` |
| Shell capture race | `/tmp/opencode/a4c-diag/shell-probe.py` (env `PROBE_RETRY=1` hoặc `PROBE_SLEEP_BEFORE_CAPTURE=3`) |
| Notification race | `/tmp/opencode/a4c-diag/notif-probe` (log trong `/tmp/opencode/a4c-diag/`) |
| Canvas.save probe | `/tmp/opencode/a4c-diag/canvas-variants.qml` + `.log` |
| Fixture clipboard proof | `/tmp/opencode/a4c-diag/fixture-fix-proof.py` + `.log` |
| Demo guard probe | `/tmp/opencode/a4c-diag/clip-demo-probe` (argv `--state`, `started:false`) |

Evidence gốc: `/tmp/opencode/a4c-g4/`, `/tmp/opencode/a4c-g4-run2/`, `/tmp/opencode/a4c-diag/`.
