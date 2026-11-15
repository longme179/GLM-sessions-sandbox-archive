# A4c C3 — L2 live test (owner-assisted runbook + report)

- **Trạng thái:** **ĐÃ CHẠY** — 2026-11-15 18:41–19:07 (+07), owner có mặt tại máy.
- **Kết quả:** **4/4 mục PASS** trên native path; phát hiện **2 bug thật** (F1 idle first-enable stall, F2 PowerMenu suspend pre-lock bằng swaylock) — **không sửa trong buổi**.
- **Shell live baseline:** PID `1315627`, IPC `lock status` = `unlocked`, repo `753dbc6` (clean, không code change).
- **Prefs baseline:** `/tmp/opencode/a4c-c3/prefs-before.json`, sha256 `f40cc56d73c132d12319a0e9ab5308c0ae9c0c7c9a947dfeb574246a394ee34a`.
- **Nguồn checklist:** plan A4c §10; lockscreen plan `2026-11-13-lockscreen-port-plan.md` mục 5 Phase 2.
- **Nguyên tắc:** mục nào fail → **không sửa trong buổi**; ghi evidence, mở issue/plan riêng (revert-don't-fix-forward).
- **Ghi chú thời điểm:** chạy buổi tối theo yêu cầu owner (override preference “ban ngày”); owner ngồi tại máy suốt run.

---

## 0. Pre-flight (Agent-1, trước khi owner thao tác)

Ghi lại baseline:

```bash
date -Is
pgrep -af 'deployment/bin/quickshell -c lme-shell'
quickshell -c lme-shell ipc call lock status
jq '{idleEnabled, idleProfiles, idleLockBeforeSleep}' ~/.config/lme-shell/settings.json
cp -a ~/.config/lme-shell/settings.json /tmp/opencode/a4c-c3/prefs-before.json
sha256sum /tmp/opencode/a4c-c3/prefs-before.json
```

Baseline thực tế (2026-11-15 18:34–18:41):

```json
{
  "idleEnabled": false,
  "idleProfiles": {
    "ac": {"display": 10, "lock": 15, "suspend": 0},
    "battery": {"display": 3, "lock": 5, "suspend": 15}
  },
  "idleLockBeforeSleep": true
}
```

Safety checklist:

- [x] Owner có mặt tại máy suốt run; chạy buổi tối theo yêu cầu owner (override “ban ngày”).
- [x] Escape hatch 1: swaylock fallback đã kiểm tra tồn tại **và thực sự chạy được** — owner thấy màn swaylock ở lần PowerMenu suspend 18:52 (xem F2).
- [x] Escape hatch 2: demo escape hatch chuẩn bị sẵn trên workspace khác; không dùng đến.
- [x] Journal capture: user journal + system journal + poll `lock status` 0.5s ghi ra `/tmp/opencode/a4c-c3/`.
- [x] Không quay video (optional); owner quan sát trực tiếp + xác nhận bằng lời.
- [x] Đã lưu `settings.json` baseline + biết cách restore; diff cuối buổi chỉ khác wallpaper do playlist shuffle.
- [x] Không chạy khi có tác vụ dài không thể gián đoạn.

Captures:

```text
/tmp/opencode/a4c-c3/journal.log          # journalctl --user -f
/tmp/opencode/a4c-c3/system-journal.log   # journalctl -f
/tmp/opencode/a4c-c3/suspend-poll.log     # lock status mỗi 0.5s
/tmp/opencode/a4c-c3/timeline.md          # timeline scratch
/tmp/opencode/a4c-c3/closeout.txt         # trạng thái cuối buổi
```

---

## 1. Nghiệm thu 1 — Idle timeout khóa đúng

Thao tác owner/agent:

1. Mở Settings → Idle; bật `idleEnabled`; đặt profile AC `lock = 1` phút, `display`/`suspend` = 0 (tránh sleep ngoài kịch bản).
2. Xác nhận helper đã áp dụng: `pgrep -af swayidle` và journal có dòng argv mới.
3. Chờ hết timeout, không chạm chuột/bàn phím.
4. Kiểm tra: `quickshell -c lme-shell ipc call lock status` → `locked`/`secure`.
5. Journal: dòng lock do `idle_control.py`/`idle_control.py lock` (hoặc native activate).

Evidence:

- [x] Timestamp bật pref + timeout.
- [x] Output `lock status` trước/trong/sau.
- [x] Journal excerpt (helper lock + lock surface).
- [x] Owner xác nhận màn khóa native (không phải swaylock) và mở khóa được.

**Kết quả: PASS** — nhưng lần bật idle đầu tiên bị stall (F1).

Timeline:

```text
18:41:25  baseline prefs saved; hash f40cc56d…; lock status=unlocked
18:44:24  owner bật idle, AC lock=1 / display=0 / suspend=0
          → FAIL lần đầu: idleStatus running=false, error "swayidle stopped: "
            pgrep -af swayidle = rỗng (F1)
18:48:19  owner toggle idle off/on → helper chạy lại
          argv: swayidle -w timeout 60 python3 .../idle_control.py lock
                before-sleep .../idle_control.py prepare-sleep
                after-resume .../idle_control.py resume
18:49:47.679  niri: INFO niri::niri: locking session
18:49:51      lock status=secure
18:49:56.855  niri: INFO niri::niri: unlocking session (owner nhập mật khẩu)
18:50:01…     lock status=unlocked
```

Journal excerpt:

```text
Nov 15 18:49:47.679052 fedora niri[3753]: 2026-11-15T11:49:47.679025Z  INFO niri::niri: locking session
Nov 15 18:49:56.855599 fedora niri[3753]: 2026-11-15T11:49:56.855568Z  INFO niri::niri: unlocking session
```

---

## 2. Nghiệm thu 2 — Suspend thủ công có before-sleep `secure` TRƯỚC khi ngủ

Thao tác:

1. Giữ `idleLockBeforeSleep = true`.
2. Owner chạy suspend từ power menu (hoặc `systemctl suspend` nếu muốn test external path — ghi rõ đường nào).
3. Trong journal, tìm handshake `prepare-sleep` + trạng thái `secure` **trước** dòng suspend/PM.
4. Xác nhận inhibitor được giữ đủ trong cửa sổ logind (budget 4s; `InhibitDelayMaxSec` 5s).

Evidence:

- [x] Timestamp suspend request.
- [x] Journal excerpt theo thứ tự: `prepare-sleep` → `secure`/ready-fd → sleep.
- [x] Không có dòng fallback swaylock ngoài dự kiến — **external path sạch**; PowerMenu path có fallback (F2).
- [x] `lock status` ngay trước khi ngủ.

**Kết quả: PASS cho external path; FAIL cho PowerMenu path (F2).**

### 2a. PowerMenu suspend — FAIL (F2)

Lần đầu owner suspend từ Power Menu. Trật tự journal cho thấy backend cũ **pre-lock bằng swaylock trước khi logind announce**:

```text
18:52:13.660  session-lock.guard mtime (secure_lock bắt đầu)
18:52:13.673  niri: locking session          ← swaylock đã chiếm session lock
18:52:13.734  systemd-logind: The system will suspend now!
18:52:17.619  kernel: xhci_hcd … failed to suspend async: error -16  ← attempt 1 abort
18:52:18.517  kernel: PM: suspend exit
18:52:29.231  niri: unlocking session        ← owner mở swaylock
18:52:56.693  niri: locking session          ← retry PowerMenu, swaylock lại pre-lock
18:52:56.726  session-lock.json mtime
18:52:56.751  systemd-logind: The system will suspend now!
18:52:57.056  Performing sleep operation 'suspend'
18:53:11.699  System returned from sleep operation 'suspend'
18:53:28.914  niri: unlocking session        ← owner mở swaylock sau resume
```

Owner xác nhận sau resume thấy **swaylock**, không phải lock screen của shell. Đây là F2: `scripts/desktop_backend.py` vẫn xử lý `action == "suspend"` bằng `lock_session(suspend=True)` → `secure_lock()` (swaylock) khi status `unlocked`, rồi mới `systemctl suspend`; vì vậy `prepare-sleep` thấy `swaylock_engaged()` và thoát sớm — native before-sleep handshake không bao giờ chạy.

### 2b. External path `systemctl suspend` — PASS

Để test đúng native before-sleep, suspend trực tiếp (bỏ qua backend):

```text
18:55:53  prepareSleep IPC thủ công:
          status_before=unlocked → prepareSleep=locking → status_after=secure
          → deactivate → status_final=unlocked   (handshake < 1s)

18:57:27.143991  systemd-logind: The system will suspend now!
18:57:27.271396  session-lock-v2.state = locked   (mtime)
18:57:27.368843  niri: INFO niri::niri: locking session
18:57:27.519826  Starting systemd-suspend.service
18:57:27.534074  Performing sleep operation 'suspend'
18:57:39.304035  System returned from sleep operation 'suspend'
```

- Không có swaylock trong suốt run (`pgrep -af swaylock` rỗng).
- Handshake 18:57:27.143 → 18:57:27.534 = **0.391s**, thừa trong budget 4s / `InhibitDelayMaxSec` 5s.
- Sau resume `lock status = secure`; `session-lock-v2.state` = `locked`.

---

## 3. Nghiệm thu 3 — Resume: focus lock surface + mở khóa

Thao tác:

1. Sau resume, quan sát: lock surface có focus không; gõ thử phím (không nhập mật khẩu) xem có nhận không.
2. Nếu mất focus: ghi rõ hiện tượng + thời điểm; heartbeat phải cứu trong thời gian ngắn.
3. Owner nhập mật khẩu đúng → desktop mở.
4. Kiểm tra `lock status` = `unlocked`.

Evidence:

- [x] Thời điểm resume (journal).
- [x] Dòng `resume`/`lock focus` của helper.
- [x] `lock status` sau resume và sau unlock.
- [x] Ghi chú focus (có/không, độ trễ).

**Kết quả: PASS.**

Timeline:

```text
18:57:39.304  resume; lock status=secure
              owner: thấy lock screen native; ô mật khẩu nhận phím ngay;
              gõ vài ký tự không Enter → hiển thị đúng; nhập mật khẩu → mở khóa
18:58:13.337  niri: INFO niri::niri: unlocking session
              shell log: pam.subprocess: Authenticated successfully
18:58:13.337  session-lock-v2.state = unlocked
```

- Focus: owner báo nhận phím ngay, không quan sát thấy mất focus; heartbeat 2s không cần can thiệp.
- Đây là lần resume của external path (native lock). Lần resume PowerMenu 18:53 không dùng được để đánh giá focus native vì swaylock đã pre-lock (F2).

---

## 4. Nghiệm thu 4 — `idleLockBeforeSleep=false`

Thao tác:

1. Tắt `idleLockBeforeSleep`.
2. Suspend thủ công → resume: kỳ vọng **không** hiện màn khóa, về thẳng desktop.
3. Bật lại `idleLockBeforeSleep=true`.
4. Restore `idleProfiles` + `idleEnabled` baseline (mục 0).

Evidence:

- [x] Journal không có `prepare-sleep`/lock activation trong lần suspend này.
- [x] Poll `lock status` toàn `unlocked`; không có swaylock.
- [x] Owner xác nhận desktop, không lock.
- [x] Prefs sau restore khớp baseline (idle prefs; wallpaper khác do playlist shuffle).

**Kết quả: PASS.**

Chi tiết procedure: sau khi tắt `idleLockBeforeSleep`, prefs cũng ghi nhận `idleEnabled=false` và helper swayidle dừng. Để test đúng gate của pref (không test nhầm “cả idle đều tắt”), owner bật lại **Idle master** và giữ **Lock before sleep OFF**:

```text
19:01:57  idleEnabled=true, idleLockBeforeSleep=false
          argv: swayidle -w timeout 60 python3 .../idle_control.py lock
                after-resume python3 .../idle_control.py resume
          → KHÔNG có before-sleep
          lock status=unlocked; không swaylock

19:02:15.799  systemd-logind: The system will suspend now!
19:02:16.105  Performing sleep operation 'suspend'
19:03:47.715  System returned from sleep operation 'suspend'
```

Poll log:

```text
19:02:16 unlocked
19:02:17 unlocked
19:02:18 unlocked
   … GAP 88.9s (suspend window) …
19:03:47 unlocked
19:03:48 unlocked
   … toàn unlocked …
```

- Không có dòng `locking session` trong journal của lần suspend này.
- `session-lock-v2.state` vẫn là `unlocked`, mtime `18:58:13.336` (không bị ghi đè).
- Không swaylock; owner xác nhận resume về thẳng desktop.

Restore (19:06):

```json
{
  "idleEnabled": false,
  "idleProfiles": {
    "ac": {"display": 10, "lock": 15, "suspend": 0},
    "battery": {"display": 3, "lock": 5, "suspend": 15}
  },
  "idleLockBeforeSleep": true
}
```

`diff -u prefs-before.json settings.json`: chỉ khác `wallpaper` (`wallhaven-21oyv6.jpg` → `wallhaven-6llg7q.jpg`) do shell có playlist shuffle wallpaper; toàn bộ idle prefs khớp baseline. Không restore wallpaper để tránh đổi lại giữa playlist.

---

## 5. Kết thúc buổi (bắt buộc)

```bash
kill "$(cat /tmp/opencode/a4c-c3/journal.pid)" 2>/dev/null || true
kill "$(cat /tmp/opencode/a4c-c3/system-journal.pid)" 2>/dev/null || true
kill "$(cat /tmp/opencode/a4c-c3/suspend-poll.pid)" 2>/dev/null || true
quickshell -c lme-shell ipc call lock status     # phải = unlocked
pgrep -af 'deployment/bin/quickshell -c lme-shell' # shell còn sống
jq '{idleEnabled, idleProfiles, idleLockBeforeSleep}' ~/.config/lme-shell/settings.json
diff -u /tmp/opencode/a4c-c3/prefs-before.json ~/.config/lme-shell/settings.json
```

Checklist đóng:

- [x] Prefs đã restore — idle prefs khớp baseline; chỉ wallpaper khác do playlist shuffle (ghi rõ, không phải test side effect).
- [x] `lock status=unlocked`.
- [x] Shell PID `1315627` healthy, không crash loop.
- [x] Journal log + evidence lưu tại `/tmp/opencode/a4c-c3/`; closeout tại `closeout.txt`.
- [x] Không fix trong buổi; 2 bug thật + 1 environmental note được ghi thành finding.

Closeout:

```text
CLOSEOUT 2026-11-15T19:07:22+07:00
lock=unlocked
1315627 /home/kimhoanglong/.local/share/lme-shell/deployment/bin/quickshell -c lme-shell --no-duplicate
swaylock/swayidle: none
captures: none
```

---

## 6. Tổng kết

| Mục | Kết quả | Evidence |
|---|---|---|
| 1. Idle timeout khóa | **PASS** | niri `locking session` 18:49:47.679; `secure` 18:49:51; unlock 18:49:56.855. F1: lần enable đầu stall, toggle off/on mới chạy. |
| 2. Suspend + before-sleep secure | **PASS (external) / FAIL (PowerMenu)** | External: logind 18:57:27.143 → v2 `locked` 27.271 → niri lock 27.368 → sleep 27.534; resume 39.304 `secure`. PowerMenu 18:52: niri lock **trước** logind, swaylock pre-lock (F2). |
| 3. Resume focus + unlock | **PASS** | Resume 18:57:39.304 `secure`; owner nhập phím/mật khẩu OK; niri unlock 18:58:13.337; PAM auth success. |
| 4. `idleLockBeforeSleep=false` | **PASS** | swayidle argv không có `before-sleep`; suspend 19:02:15.799 → resume 19:03:47.715; poll toàn `unlocked`, không lock activation; owner thấy desktop. |

**Kết luận chung:** Native lock đạt **L2 trên native/external path**: idle lock, before-sleep handshake, resume focus + PAM unlock, và pref gate `idleLockBeforeSleep=false` đều PASS. **Chưa thể sign-off A4c** vì PowerMenu suspend vẫn đi qua legacy backend và pre-lock bằng swaylock (F2); thêm F1 làm idle im lặng không chạy ở lần bật đầu. Cả hai không sửa trong buổi; chuyển Agent-2 lập plan/PR riêng.

---

## 7. Findings (không sửa trong buổi)

### F1 — Idle first-enable stall (product bug, P1)

- **Hiện tượng:** 18:44:24 owner bật Idle + đặt AC `lock=1/display=0/suspend=0`. `idleStatus` trả `running:false`, `error:"swayidle stopped: "`; `pgrep -af swayidle` rỗng. Toggle idle off/on lúc 18:48:19 thì helper chạy đúng.
- **Impact:** lần bật idle đầu tiên có thể không chạy helper → idle lock không được enforce mà UI không báo rõ; user phải toggle lần nữa.
- **Nghi vấn:** race readiness/first-enable trong `qml/services/IdleState.qml` (helper start trước khi profile/backend sẵn sàng); có thể liên quan 2 readiness race đã ghi trong C2 §7.4 (`idleStatus` truthy trước `backendReady`). Cần Agent-2 đọc code + plan điều tra, không kết luận sớm.
- **Evidence:** `/tmp/opencode/a4c-c3/timeline.md`; phiên IPC lúc 18:44:24 (trong conversation); không có log helper vì process không tồn tại.

### F2 — PowerMenu suspend pre-lock bằng swaylock (product bug, P1)

- **Hiện tượng:** PowerMenu suspend 18:52: niri `locking session` **trước** logind `The system will suspend now!`; `session-lock.json`/guard mtime 18:52; resume 18:53:11 hiện swaylock (owner xác nhận). Retry 18:52:56 lặp lại.
- **Root cause:** `scripts/desktop_backend.py` vẫn xử lý `action == "suspend"` → `lock_session(suspend=True)` → `secure_lock()` (swaylock) khi status `unlocked`, rồi `systemctl suspend`. `prepare_sleep` sau đó thấy `swaylock_engaged()` và return sớm → native lock không tham gia.
- **Impact:** đường suspend phổ biến nhất (PowerMenu) bỏ qua native lock và before-sleep handshake; trái với thiết kế L2.
- **Fix direction (để Agent-2 plan):** route PowerMenu suspend qua native lock/`prepareSleep` hoặc gọi `systemctl suspend` trực tiếp để swayidle `before-sleep` xử lý; bỏ `secure_lock()` khỏi suspend path (giữ fallback có kiểm soát). Cần test cho cả `idleLockBeforeSleep=true/false`.
- **Evidence:** `/tmp/opencode/a4c-c3/system-journal.log` dòng 11–12, 746–747; `session-lock.json` mtime; owner quote; so sánh trật tự external path 18:57.

### F3 — Environmental: xhci suspend abort (không phải shell bug)

- 18:52:17.619 kernel `xhci_hcd 0000:06:00.4: failed to suspend async: error -16` làm attempt 1 abort; retry 18:52:56 ngủ thật. Không lặp lại ở 18:57/19:02. Ghi nhận để loại trừ khỏi bug shell; nếu tái diễn nhiều lần, mở issue phần cứng/kernel riêng.

### Quan sát thêm (chưa phân loại)

- `qml/features/lock/LockArtQuantizer.qml:34: Error: drawImage(), type mismatch` xuất hiện mỗi lần lock surface hiện; lock vẫn hoạt động bình thường, owner không báo lỗi hình ảnh. Chưa đủ evidence để kết luận; không đưa vào scope Agent-2 đợt này trừ khi liên quan trực tiếp F1/F2.

---

## 8. Next

1. **Agent-2 plan** cho: (a) test/fixture gitignored sau Q5 + readiness + PDEATHSIG + `Canvas.save()` drawing fixture (owner đã duyệt sửa test/fixture), (b) **1 PR clipboard** gộp `ClipboardPanel.qml:127 previewClose` + `ClipboardState.qml:173` demo guard, (c) F2 PowerMenu suspend, (d) F1 idle first-enable stall.
2. **PR riêng cho F2** (và F1 nếu Agent-2 tách) — không gộp vào PR clipboard/test.
3. Không sửa assertion hiện có nếu chưa hỏi owner; tests are gitignored.
4. Repo clean tại `753dbc6`; mọi implementation sau này làm trong worktree riêng, không đụng live shell.
