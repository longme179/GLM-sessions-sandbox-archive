# LME SHELL — KẾ HOẠCH TIẾP QUẢN: ĐÓNG Q4 + MỞ Q5

**Ngày:** 2026-11-11 (phiên Qwen, ~19:45–20:10 +07) · **Trạng thái:** CHỜ CHỦ REPO DUYỆT — chưa code
**Repo:** `longme179/lme-fedora-niri-qs` @ `main` **a1bc941** · **Máy:** Fedora 44, niri 26.04, quickshell 0.3.2-1.fc44
**Phiên trước:** GLM — PR #126 + #127 (Q4 legs 2–3 display/mirror + night-light/idle)
**Nguyên tắc phiên này:** chỉ planning + reconnaissance. Không sửa repo, không sửa prefs, không restart shell.
Mọi probe đều read-only hoặc chạy offscreen trong `/tmp/lme-cap-probe` (XDG riêng).

---

## 0. TL;DR — 5 điều chủ repo cần biết ngay

1. **#127 đã merge và shell đã restart rồi.** Máy pull `a1bc941` lúc 03:50:49, shell PID 1960309 khởi động 03:51:03 → bản đang chạy **đã có hotfix-2** (mirror stop-clear). Việc "merge #127 + restart" trong tổng kết phiên trước **đã xong**, không cần làm lại.
2. **Shell khỏe: 16 giờ, 0 lỗi.** 0 crash mới, 0 `TypeError`/QML error trong log sống. Drift chỉ còn 2 loại đã biết (Q2 apps superset, Q1 wifi strength jitter). PSS 208 MB / ngưỡng 400 MB.
3. **Nhưng checklist Leg 3 CHƯA hề được chạy thật:** `nightLightEnabled = false`, `idleEnabled = false` → không có tiến trình `wlsunset`/`swayidle` nào, log 16 h không nhắc một chữ. Mirror cũng chưa test được vì máy chỉ có **eDP-1**. Nghĩa là: code đã verified bằng test, **chức năng thì chưa ai bấm thử**.
4. **Phát hiện mới làm thay đổi giả định của plan:** máy có `Qt.labs.folderlistmodel` (liệt kê thư mục) và `QtQuick.LocalStorage` (SQLite), và `FileView` **tự tạo thư mục cha khi ghi**. Ba điều này bác bỏ một phần danh sách "blocker" mà plan Q2/Q4/Q5 đang dựa vào → Q5 nên được chia lại leg.
5. **Còn 3 tiến trình quickshell offscreen sót lại** từ đợt verify Q4 (19 giờ tuổi, ~25 MB RSS mỗi cái) + 2 worktree cũ. Cần chủ repo cho phép dọn.

---

## 1. Trạng thái đã xác minh trên máy thật (máy đo, không phải suy đoán)

| Hạng mục | Kết quả | Nguồn |
|---|---|---|
| HEAD máy | `a1bc941` = main, working tree sạch | `git log`, `git status -sb` |
| #126 / #127 | merged 02:44 / 03:50:49 +07 | GitHub API + `git reflog main` |
| Shell sống | PID 1960309, start 03:51:03 +07, uptime ~16 h | `ps -o lstart` |
| Backend | PID 1960326 chạy `--no-session-daemons` ✓ (ownership split hoạt động) | `pgrep -af desktop_backend` |
| Crash | 16 thư mục, mới nhất 00:35 (trước restart) → **0 crash mới** | `~/.cache/quickshell/crashes` |
| Log sống | `/run/user/1000/quickshell/by-id/1l0614l0bot/log.log` (193 KB) | `/proc/1960309/fd` |
| Lỗi trong log | 0 ERROR, 0 TypeError/ReferenceError, 0 QML error | grep trên log sống |
| Drift 16 h | **948×** `[Q2 A/B] apps 57 vs 62` (superset đã biết) · **116×** `[Q1 A/B] network` strength 65↔70 (poll lag đã biết) · 0 mục Q3/Q4 | grep + uniq -c |
| Bộ nhớ | PSS 208.06 MB (QS 159.2 + backend 31.1 + clipboard worker 7.1 + helpers) | `memory_report.py --label planning-probe` |
| Daemon | không có `wlsunset`/`swayidle`/`wl-mirror` nào | `pgrep -a` |
| Màn hình | chỉ **eDP-1** (Lenovo 0x9059, 1920×1080@120.002, VRR supported) | `niri msg --json outputs` |
| Công cụ | wlsunset/swayidle/wl-mirror/grim/wf-recorder/wl-paste/wl-copy/gowall/awww **có**; **satty THIẾU** | `command -v` |

**Prefs liên quan (đọc, không sửa):** `nightLightEnabled=false`, mode `manual`, 4500K, 20:00→07:00 ·
`idleEnabled=false`, profiles AC {display 10, lock 15, suspend 0} / battery {3, 5, 15}, `idleLockBeforeSleep=true` ·
`mirroringEnabled=true`, `displayLayout=[]` · `recordingEnabled=true`.

**Hai ghi chú trung thực:**
- Log `~/.local/state/lme-shell/log/lme-shell.log` **cũ** (ghi lần cuối 9 Nov 19:45) vì shell được mở tay bằng `quickshell -c lme-shell` từ fish, không qua `scripts/start.sh` (script mới redirect stderr vào log xoay vòng — `start.sh:101-109`). Bằng chứng drift vẫn lấy được từ `log.log` của instance đang chạy.
- Những dòng `[Q1 A/B] battery ... vs native [true,1,false,true]` trong log cũ là **lịch sử trước hotfix #116** (UPower 0–1 fraction). Code hiện tại đã có `percent100()`; log sống 16 h **không còn** dòng battery nào. Không phải bug đang mở.

---

## 2. Phát hiện năng lực mới (probe offscreen, có bằng chứng)

Chạy `quickshell -p /tmp/lme-cap-probe/probeE.qml`, `QT_QPA_PLATFORM=offscreen`, XDG tạm. Kết quả ghi ra file:

```
backlight count=1 first=amdgpu_bl1
procnum  count=414 first=1
hwmon    count=8 first=hwmon0
sqlite   rows=1 a=hello b=7
```

| Năng lực | Kết luận | Ảnh hưởng tới plan |
|---|---|---|
| `Qt.labs.folderlistmodel` | **CÓ và chạy được** — liệt kê `/sys/class/backlight`, `/sys/class/hwmon`, `/proc/<pid>` | Bác bỏ blocker "quickshell 0.3.2 không có API liệt kê thư mục" đang chặn **tempC / brightness / monitor processes** (Q2 transitional) và gây khó cho **file_search / wallpaper** (Q5) |
| `QtQuick.LocalStorage` | **CÓ và chạy được** — CREATE/INSERT/SELECT OK, DB ở `$XDG_DATA_HOME/quickshell/QML/OfflineStorage/Databases/<hash>.sqlite` | Mở đường cho **clipboard sqlite** (Q5) — nhưng đường dẫn DB cố định, phải migrate schema + vẫn còn bài toán wl-paste watcher |
| `FileView.setText` | **Tự tạo thư mục cha** (`nested/deeper/file.json` được tạo từ số 0, nội dung đúng) | Blocker "không có mkdir" trong đề xuất giữ capture/recording backend-fed **không còn đúng nguyên văn** |
| Chưa kiểm chứng | đọc/ghi **binary** (PNG signature), `chmod`, exclusive-create, `stat` | Vẫn là lý do chính đáng để capture/recording ở lại backend thêm một phase |

**Gotcha ghi lại cho phiên sau:** `/usr/bin/qml` là **Qt5** (`qt5-qtdeclarative-devel`) → probe Qt6 bằng nó luôn ra "Did not load any objects"; phải dùng `quickshell -p`. `console.log` của probe không ra stdout ổn định → cho probe **ghi kết quả bằng FileView ra file**. `FolderListModel` với `nameFilters:["thermal_zone*"] showDirs:false` trả 0 (symlink tới thư mục bị coi là dir) — cần `showDirs:true`, chưa verify lại.

**Bối cảnh phiên bản:** upstream quickshell vẫn ở **v0.3.2** (release 2026-10-08, master `9b0f339` 2026-10-17). Không có bản mới để "chờ rồi port" — mọi quyết định phải dựa trên 0.3.2 + các module Qt6 đã cài.

---

## 3. Việc cần dọn (cần chủ repo OK, đều là hành động phá hủy nhỏ)

| # | Việc | Lý do | Rủi ro |
|---|---|---|---|
| H1 | Kill 3 quickshell offscreen sót: **1760540 / 1761126 / 1764612** (start 00:35–00:38, `QT_QPA_PLATFORM=offscreen`, `XDG_CONFIG_HOME=/tmp/tmp*`) | Tàn dư gate Q4, 19 h tuổi, ~77 MB RSS cộng lại, làm nhiễu `memory_report` ("Unattributed Quickshell PIDs") | Thấp — không phải cửa sổ người dùng; xác minh lại env trước khi kill |
| H2 | Prune worktree `/tmp/q4-verify` (d271fa4) và `~/lme-q4-verify` (81bd66d) | Đã verify xong #127 | Thấp — kiểm tra `git status` từng cái trước |
| H3 | Lần restart tới: mở bằng `scripts/start.sh` (hoặc `... 2>&1 \| tee`) | Để log xoay vòng `~/.local/state/lme-shell/log/` được ghi, gom drift cả ngày dễ hơn | Không — chỉ đổi cách khởi động |

---

## 4. Bước 1 — ĐÓNG Q4 (đề xuất làm trước, phạm vi nhỏ)

### 4a. Checklist chạy thật cho Leg 2/3 (agent làm, có STOP-gate)

Kịch bản: backup `settings.json` → bật từng tính năng → đo → **restore nguyên trạng**. Không đụng cửa sổ người dùng, không sửa niri config.

| # | Thao tác | Tiêu chí pass đo được |
|---|---|---|
| C1 | Bật Night Light `manual` | `pgrep -a wlsunset` đúng 1 child, argv `-T … -t …` khớp `night_light.py`; PPID trỏ về shell/helper; màn đổi màu thật (chủ repo xác nhận bằng mắt) |
| C2 | Đổi `schedule` + place | wlsunset restart **chỉ khi signature đổi**; giờ sunset khớp Almanac (đã parity 13 case) |
| C3 | Tắt Night Light | child biến mất, không mồ côi |
| C4 | Bật idle, đang cắm AC | `pgrep -a swayidle` argv **shlex-joined** giống hệt `idle_control.py::idle_command` với profile AC {10,15,0} |
| C5 | Rút sạc (hoặc mô phỏng `acOnline`) | argv đổi sang profile battery {3,5,15}; `idleLockBeforeSleep` giữ đúng |
| C6 | `stayAwake` | inhibit bật/tắt, swayidle tương ứng |
| C7 | Restart shell | **0 wlsunset/swayidle mồ côi** sau restart (PDEATHSIG), shell mới sở hữu lại đúng 1 child mỗi loại |
| C8 | Displays page + mirror control | trang hiện đúng eDP-1/mode list; bấm mirror khi chỉ có 1 màn → **đúng thông báo từ chối** của backend (parity lỗi) |
| C9 | Sau tất cả | restore prefs về đúng giá trị cũ (diff = rỗng), 0 crash mới, 0 ERROR mới trong log |

**Mirror round-trip 2 màn:** `niri msg` 26.04 **không có lệnh tạo virtual output** (`output` chỉ off/on/mode/scale/transform/position/vrr). Nên: hoặc chủ repo cắm màn ngoài rồi làm C8-full, hoặc ghi nhận trung thực "needs real-session check với 2 màn" như các phase trước.

### 4b. Quyết định capture/recording

Đề xuất của phiên trước: **giữ backend-fed** vì thiếu mkdir/stat/chmod/binary-read. Sau probe hôm nay: mkdir đã có, còn binary/chmod/exclusive-create **chưa kiểm chứng**. Ba lựa chọn:

- **(A) Giữ backend-fed, chốt ở Q6** — khuyến nghị. Rẻ nhất, đúng tinh thần "gradual", không đụng chuỗi grim/wf-recorder/satty đang chạy ổn. Ghi rõ lý do đã cập nhật trong STATE.
- (B) Probe thêm 1 lượt (binary read qua `FileView.data`, chmod, exclusive create) rồi mới quyết — tốn ~1 buổi nhỏ.
- (C) Port luôn Q4 capture/recording — không khuyến nghị: `satty` còn **thiếu trên máy**, không verify nổi chuỗi annotation.

### 4c. Deliverable

PR **docs-only** kiểu #122 ("Q3 closed"): `docs/STATE.md` + `MIGRATION_LOG.md` + `CHANGELOG.md` ghi Q4 closed, kèm bảng machine-verified / owner-side còn lại. Gate: **G0 only** (theo AGENTS.md cho docs-only). Chủ repo merge.

---

## 5. Bước 2 (tùy chọn) — "Q4.5": trả nợ 3 key transitional của Q2

Nhờ `FolderListModel`, ba key đang phải nuôi backend có thể về native:

| Key | Đường đi mới | Ghi chú |
|---|---|---|
| `brightness` (read) | FolderListModel `/sys/class/backlight` → FileView `actual_brightness`/`max_brightness` | máy có đúng 1 entry `amdgpu_bl1` |
| `tempC` | FolderListModel `/sys/class/hwmon` (8 entry) → đọc `name`/`temp*_input` | phải giữ đúng quy tắc chọn sensor của `system_monitor.py` |
| monitor `processes`/`processCount` | FolderListModel `/proc` nameFilters số (414 entry) → FileView `stat`/`comm` | **chi phí**: nhiều FileView cùng lúc; cần đo lại wake-rate + PSS, giữ cadence 2 s, không đổi hành vi |

Giá trị: xóa 3 ngoại lệ "transitional" + các emit site `DEPRECATED(Q2->Q6)`, giảm bề mặt backend trước Q6.
Rủi ro: `/proc` scan bằng hàng trăm FileView có thể đắt hơn Python hiện tại → **phải đo**, nếu tệ hơn thì giữ Python và ghi lại trung thực. Đây là lý do bước này tách riêng, không nhét vào Q5.

---

## 6. Bước 3 — Q5 CHIA LẠI LEG (dựa trên năng lực thật, không theo bản plan cũ)

Tổng Q5 = **1.760 dòng Python** (đo bằng `wc -l` hôm nay, khớp plan §5).

| Leg | Gia đình | Dòng | Cơ chế | Rủi ro / blocker còn lại |
|---|---|---|---|---|
| **A — network/content** | `weather` 208 + `weather_actions` 48 + `lyrics` 137 | **393** | `XMLHttpRequest` (QtNetwork có sẵn) + FileView cache (mkdir đã ổn) | Lyrics đọc **tag nhúng trong file nhạc** = binary read → phần đó giữ backend hoặc chỉ port LRC + LRCLIB. Timeout/backoff phải giữ đúng shape lỗi |
| **B — wallpaper + search** | `wallpaper` 234 + `wallpaper_actions` 114 + `wallpaper_palette` 51 + `gowall_actions` 48 + `palette_actions` 39 + `file_search` 41 + `file_search_actions` 31 | **558** | FolderListModel liệt kê ảnh + FileView playlist; awww/gowall qua CommandRunner; search đệ quy bằng `find` (Process) hoặc model lồng | `fcntl` lock của playlist → phải tái tạo semantics single-writer; đệ quy nhiều tầng bằng QML model có thể chậm |
| **C — equalizer + visualizer** | `equalizer_actions` 424 + `audio_visualizer` 70 | **494** | `ctl` protocol qua Process; cava child sở hữu qua helper PDEATHSIG (pattern đã có từ Leg 3) | `wave` sinh tone preview = **binary write** → giữ Python phần đó; cap 250 dòng buộc phải tách file |
| **D — clipboard** | `clipboard` 315 | **315** | LocalStorage (sqlite) + wl-paste/wl-copy watcher | **Cao nhất**: DB path cố định của LocalStorage ≠ path hiện tại → migration; watcher là child sống lâu (Q-3, đã từng regression mồ côi). Khuyến nghị **để cuối hoặc giữ Python** |

**Thứ tự đề xuất:** A → B → C → (D quyết riêng). Mỗi leg = 1 nhánh, tests → impl → docs, **một review-stop**, chủ repo merge.
**Kỳ vọng thực tế:** mỗi leg cần **1 phiên + 1–2 vòng hotfix trên máy thật** — cả 3 leg Q4 đều lộ bug ở lần chạy engine đầu tiên mà sandbox không thấy. Đừng hẹn "xong trong 1 lượt".

**Gate mỗi leg (theo AGENTS.md):** trong lúc làm G0 + G1 + native case liên quan; trước merge chạy G0–G4 + G6 **một lần**; 10 lần cold launch preview/Settings (main vs head, median) + RSS ở 10 s; hỏi chủ repo nếu Settings >+100 ms hoặc RSS >+10%. Không sửa assertion cũ khi chưa hỏi. Không tự merge/push main.

---

## 7. Câu hỏi chờ chủ repo chốt

| # | Câu hỏi | Khuyến nghị của tôi |
|---|---|---|
| Q1 | Đóng Q4 bằng cách nào: agent chạy checklist C1–C9 (có backup/restore prefs), hay chủ repo tự bấm, hay bỏ qua sang Q5? | **Agent chạy C1–C9**, chủ repo xác nhận phần nhìn bằng mắt (màu Night Light) |
| Q2 | capture/recording: giữ backend-fed (A), probe thêm (B), hay port luôn (C)? | **A** — giữ backend-fed, chốt lại ở Q6 |
| Q3 | Sau Q4: làm Q4.5 (3 key transitional) trước, hay vào thẳng Q5 leg A? | **Q4.5 trước** nếu chấp nhận rủi ro đo đạc; nếu muốn tiến độ migration thì **Q5-A** |
| Q4 | Có màn ngoài để test mirror 2 màn không? | Nếu không: ghi nhận trung thực là hardware-check còn nợ |
| Q5 | Cho phép dọn H1/H2 (kill 3 process offscreen + prune worktree)? | **Có** — chúng là tàn dư test, không phải phiên người dùng |

---

## 8. Kỷ luật giữ nguyên (nhắc lại cho chính tôi)

- Không credential trong repo/commit/PR/output. 401 → dừng và báo cáo.
- Không bịa verification: tách rõ **machine-verified** vs **owner-side còn lại**.
- Mọi thay đổi shell: đủ battery (qmllint + check-architecture + catalog + unit + native), vì qmllint không bắt singleton thiếu `import Quickshell`.
- QML xanh trong sandbox **không có nghĩa gì** — parse/compile chỉ xảy ra với quickshell thật; luôn live-validate trước PR.
- STOP trước PR, xuất diff verbatim, chủ repo review rồi mới merge.
- Cuối phiên: cập nhật `knowledge/` + push archive.