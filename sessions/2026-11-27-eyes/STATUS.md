# perf/responsive-v2 — STATUS (hand-off, 2026-11-27 ~13:35 giờ host, phiên 6 phần 2)

Tóm tắt tiếng Việt: **mọi mục của kế hoạch phiên 6 đã chạy xong** trừ những việc cần owner quyết
(mục 9). Phía A (main) đã chạy 3 run S1/S3; bảng A vs B đã có; selftest `ghost` đã tìm ra nguyên
nhân và sửa; PR prep xong (`AGENTS.md` không còn khác main, `check.sh` rc = 0); bản PR text viết
sẵn (`PR-DRAFT.md`); đã push `b990406..a7df45c`. Kết luận chính: **fix Escape cho activity island
được xác nhận trên A so với B bằng cùng một bản harness** — trên main island không đóng bằng Escape
lần nào (0/9 bước S3, 12 lần harness phải đóng qua IPC trong 3 run), trên nhánh 9/9 (median
16.7 ms). **S1, S2 và các panel khác của S3: không thấy khác main trong 3 rep.** Click không
trượt: 54/54 điểm click vào đúng tâm nút tab ở mỗi phía. Lưu ý khi đọc số: S1/S3 mỗi phía mới có
3 rep (luật của harness là N ≥ 10). Máy sạch sau mọi run (shell deployed được khôi phục, không còn
tiến trình perf).

## 1. Trạng thái các mục

| mục | trạng thái |
|---|---|
| S2 A vs B (click bị nuốt) | xong — có sẵn trên main, không phải regression (`eyes-analysis/AB-S2-COMPARE.txt`) |
| S1/S3 chạy thật phía B (nhánh) | xong — 3 run, 0 sự cố |
| S1/S3 chạy thật phía A (main) | xong — 3 run, 14 sự cố (12 trong S3, 1 trong warm-up của S1, 1 trong warm-up của S1 fast: mục 3.1, 3.3) |
| Bảng S1/S3 A vs B | xong — `eyes-analysis/AB-S1S3-COMPARE.txt` |
| Selftest case `ghost` | xong — nguyên nhân + fix `aa77a09`, selftest 9/9 trên host |
| PR prep (revert `4469385`, `check.sh`, PR text) | xong — `check.sh` rc = 0 trên `a7df45c`; `PR-DRAFT.md` |
| Mirror archive repo | xong — xem mục 8 |
| Chạy lại N ≥ 10 mỗi phía cho S1/S3 | chưa — chờ owner (mục 9) |

## 2. Hai phía đo như nhau

- A = `p-main`: commit `8374e946beef` (main) + `--diagnostics 7fc1df9` (watchdog, không chạy nếu
  thiếu `LME_SHELL_WATCHDOG=1`). B = `p-head`: `33c687c48678` (nhánh). Probe của cả hai:
  `6fc853ea329a` (meta `provenance` của từng run ghi đúng như vậy).
- Harness = repo checkout `~/.cache/lme-perf/rv2/repo/scripts/perf`. Sáu run đều chạy trước các
  commit cuối; `git diff b990406 a7df45c` chỉ chạm `AGENTS.md`, `config/architecture.json` và
  `scripts/perf/sim.py` (mô hình offline) → code đo của 6 run và của head giống nhau.
- Đã kiểm bằng git: `33b204d` (fix shell) **không** có trong `db2facb95870`, `8374e946`; **có**
  trong `9377fbcfd476`, `249420b70958`, `33c687c`.

| phía | run (host, UTC+7) | bắt đầu | dài | problems | khôi phục |
|---|---|---|---|---|---|
| B | `20261127-122409-s1-b2` | 12:24:17 | 100.1 s | 0 | ok |
| B | `20261127-123309-s3-b2` | 12:33:17 | 111.8 s | 2 | ok |
| B | `20261127-123509-s1fast-b2` | 12:35:16 | 54.9 s | 0 | ok |
| A | `20261127-130005-s1-a` | 13:00:13 | 103.1 s | 1 | ok |
| A | `20261127-130157-s3-a` | 13:02:03 | 143.4 s | 12 | ok |
| A | `20261127-130427-s1fast-a` | 13:04:33 | 55.1 s | 1 | ok |

Cả 6 run: `ended: finished`, `restored: true`, `standin_left: []`, workspace trước/sau như nhau.

## 3. Kết quả A vs B (chi tiết: `eyes-analysis/AB-S1S3-COMPARE.txt`, `PEEK-*.txt`)

### 3.1 Fix shell — activity island đóng bằng Escape (thay đổi hành vi duy nhất của nhánh)

| | main (A) | nhánh (B) |
|---|---|---|
| S3, bước `activity` (3 rep × 3 bước) | 0/9 đóng bằng Escape; cả 9 lần harness đóng qua IPC | 9/9; median 16.7 ms, max 451.6 ms |
| Warm-up của S3, S1, S1 fast | 3 lần "activity stayed open after Escape" → IPC | 0 lần |
| S4 ngày 26/11 — cây nhánh trước fix / sau fix (xem `PR-DRAFT.md`) | `db2facb9`: 12 lỗi / 12 chu kỳ | `9377fbc`: 0/4; `249420b`: 0/20; run n10: 38/41, 3 lỗi lớp `frozen` |

Tổng trên main trong 3 run hôm nay: island ở lại sau Escape **12 lần**; trên nhánh **0 lần**.

### 3.2 S1 — Control Center tabs: không thấy khác main trong 3 rep

- Ordered (3 rep × 6 tab): click → built/present 8.9–16.1 ms (median từng tab, cả hai phía);
  click → settled 391–403 ms ở main; nhánh 385–397 ms trừ `notifications` (median 518 ms, max
  671 ms). Escape → gone: median 22.0 / 20.7 ms (A/B). Cả 6 rep ok.
- GUI thread vẫn đứng khi dựng page lần đầu: main `devices` settled tới 1465 ms, `agenda` 730 ms.
- Random (3 rep × 12 click): main 1 + 2 + 1 stall > 100 ms (tệ nhất 2215 ms, rep1 có 3 click
  không đo được `react_ms`); nhánh 1 + 0 + 1 (tệ nhất 3088 ms, rep0 có 5 click không đo được).
- Fast (click liên tục 3 s, ~355 click/rep): main stall 0 + 3 + 1 (tệ nhất 813 ms); nhánh
  1 + 0 + 0 (tệ nhất 279 ms, đều < 300 ms).
- Tổng 9 rep mỗi phía, stall > 100 ms: main 13 (10 cái > 300 ms, tệ nhất 2215 ms); nhánh 9
  (5 cái > 300 ms, tệ nhất 3088 ms). Khác nhau trong nhiễu của 3 rep — không kết luận được.

### 3.3 S3 — các panel khác: độ trễ như nhau, đuôi dài rơi chỗ khác nhau

- Mở: Control Center median 282.5 ms (A) / 304.0 ms (B); panel khác 104–192 ms median hai phía.
- Escape → gone (median): overlay của shell 17–49 ms hai phía; `settings` (cửa sổ riêng) 90.6 ms
  (A) / 235.8 ms (B), max 529.7 / 487.7 ms.
- Đuôi ở main: `overview` ở lại sau Escape 2 lần (1 lần Escape thứ hai, 1 lần IPC; lần IPC có
  stall 3738 ms lúc đóng); `settings` 1 lần mở 1686 ms.
- Đuôi ở nhánh: `overview` 1 lần mở 2914 ms; `notifications` 1 lần đóng 1283 ms; `launcher` và
  `power` mỗi cái 1 lần cần Escape thứ hai (rep2, stall lúc đóng 2552 / 2345 ms).
- Tổng: A 51 bước, 40 đóng thẳng, 11 bằng recovery; stall 24 / 13 / 3738 ms. B 51 bước, 49 đóng
  thẳng, 2 bằng recovery; stall 24 / 11 / 2552 ms.
- Bước workspace `skipped` cả 6 rep: workspace đang focus không có cửa sổ, rời đi sẽ làm niri xoá.

### 3.4 S2 — Settings: click bị nuốt có sẵn trên main (đã chạy ở phần 1 của phiên)

Run A `20261127-111001-s2-aside-a`, run B `20261127-041443-s2-vision2`, variant `all`, 3 rep:
A 16/54 và B 17/54 click không navigate; 16 cặp (rep, page) trùng nhau, B chỉ có thêm `about`
rep0. Chi tiết: `eyes-analysis/AB-S2-COMPARE.txt`.

### 3.5 Click có trượt không (câu hỏi của owner) — không

`eyes-analysis/S1-B2-EYES-CHECK.txt` và mục "Eyes" trong `AB-S1S3-COMPARE.txt`: 54 ảnh mỗi phía,
54/54 điểm click nằm trong rect nút tab mà harness đọc được (lề trái/phải 143–144 px, trên/dưới
20 px trên nút 287–288 × 40 → đúng tâm); hình học hai phía giống hệt nhau. Bằng chứng hành vi:
mỗi click sinh `cc.select <tab>` đúng tab sau 9–16 ms khi GUI thread rảnh. Phép thử "đo màu chạy
từ tâm ra mép nút" **không kết luận được** (chữ nhãn nằm ngay dưới crosshair) — không dùng.

## 4. Commit trên nhánh trong phiên này (đã push)

| commit | nội dung |
|---|---|
| `c2e51ba` | S1 đợi panel stage đứng yên (`STAGE_WAIT_MS`, `panel_at_rest`) trước khi đọc rect; `control_click` không click khi Control Center đã đóng; mark `cc.tab <id>`; vòng workspace an toàn; không mở lại panel sau rep cuối |
| `08da4b7` | probe map một Control (Button của QtQuick.Controls) qua `background`; `meta.still_reads` |
| `b990406` | `meta.s1_tab_rects`: rect từng nút tab mỗi rep |
| `aa77a09` | mô hình (sim.py) kết thúc burst S2 ở click cuối như kịch bản đã báo — selftest `ghost` xanh |
| `5fc777b` | revert `4469385` (ngoại lệ tạm trong `AGENTS.md`) — `AGENTS.md` không khác main |
| `29c6f81` | `config/architecture.json` về mode 644 |
| `a7df45c` | `config/architecture.json` khai báo `scripts/perf/eyes.py`, `eyes_patch_repo.py` (check.sh từng ĐỎ vì "Unclassified source") |

Các commit đều được áp bằng script sửa có neo (anchor) trong `scripts/`, bản sao ở
`eyes-analysis/tools/` (`s1s3_patch_repo.py`, `s1s3_patch3_repo.py`, `ghost_fix_repo.py`,
`arch_fix_repo.py`).

## 5. Selftest `ghost`: nguyên nhân và cách sửa

- Triệu chứng: "expected one ghosted burst, got violations=0"; đỏ cả trên bản gốc `9a81fbd` lẫn
  `e5ef1b1` (pre-existing, không ảnh hưởng số đo S2 thật).
- Nguyên nhân: `settings_burst` click qua `ctx.nav_point()` → `settled_point()`; hàm này ngủ
  0.15 s, đọc lại rect, rồi ngủ 0.25 s khi rect đã đứng yên → ~400 ms mỗi click, cộng `gap_ms`
  60 ms. Mô hình (`sim.py`) lại kết thúc burst 150 ms sau một click, nên mọi burst đều coi là
  một click; fault `s2:ghost@2` (cần ≥ 2 click) không bao giờ bắn.
- Sửa: `FakeInjector.note` đọc dòng injector `burst about+wallpaper+about gap=60` và đưa số
  click cho mô hình (`burst_plan`); burst kết thúc ở click cuối của plan. Không có plan thì giữ
  luật 150 ms. Chỉ chạm `sim.py`; kịch bản, detector, analyzer không đổi.
- Kiểm: selftest trên host 9/9 ngay sau khi áp fix (`/tmp/st-ghost.log`); trên sandbox một lần
  case `clean` đỏ khi có việc khác chạy đồng thời, chạy riêng thì xanh ở cả bản chưa vá và bản đã
  vá → flake do CPU. Ba commit sau đó (`5fc777b`, `29c6f81`, `a7df45c`) không chạm `sim.py`.

## 6. Phát hiện chưa sửa (đã báo owner)

1. **S2 variant `aba`/`toast` không còn "nhanh"**: cùng đoạn `settled_point` khiến 2 click của
   burst cách nhau 466 ms (bản ghi mô hình: 466 ms đều nhau) thay vì 60 ms cộng thời gian một
   click như thiết kế (`gap_ms=60`). Trong các run S2 còn giữ ở `runs/` (từ 26/11 18:27) không có
   run thật nào dùng `aba` hay `toast` (chỉ `all`), nên không số đo nào trong các bảng bị ảnh
   hưởng; nhưng tiêu đề kịch bản "rapid page switching" hiện không được thử đúng nghĩa. Hướng sửa:
   đọc toạ độ nav một lần cho cả burst rồi click với khoảng thiết kế — cần owner quyết vì nó đổi
   cách click (phần chờ đứng yên vốn sửa lỗi click trượt khi cuộn). Kiểm lại bằng:
   `python3 -I scripts/s2_burst_gaps.py <run dir>`.
2. **Stall GUI thread khi dựng page lần đầu** (S1: `devices`, `agenda`, `notifications`) — có ở
   cả hai phía, chưa profilé.
3. **Click Settings bị nuốt** (S2) — pre-existing, chưa tìm cơ chế.
4. **Panel đôi khi cần Escape thứ hai**: `launcher`, `power` (nhánh), `overview` (main) — chưa
   biết có cùng cơ chế focus như activity island không.
5. Số S1/S3 mỗi phía mới 3 rep; N ≥ 10 thì mới được kết luận theo luật harness.
6. Bước workspace của S3 bị skip khi workspace đang focus không có cửa sổ.
7. Chưa capture được frame của bar/overlay; VLM không dùng để phán quyết (2 lần hallucinate).

## 7. PR prep

- `PR-DRAFT.md` (tiếng Anh, theo quy ước repo): tiêu đề, tóm tắt thay đổi, bằng chứng S4 + S3,
  phần "không sửa gì trong PR này" (S1, S2, S3), checks, hướng review. Mọi số trong bản này đã
  đối chiếu lại với `summary.md` các run S4, `AB-S1S3-COMPARE.txt`, `AB-S2-COMPARE.txt` và log
  `check.sh`.
- `bash scripts/check.sh` trên `a7df45c`: rc = 0 — "Architecture: dependency, cycle and
  source-size checks passed", "Demo backend snapshot: valid", "Backend tests and Bash syntax
  checks passed"; thư mục `tests/` không có nên script tự bỏ qua.
- So với `main`, nhánh (49 commit; 44 commit chạm `scripts/perf`, 10 commit chạm file khác) chỉ
  đổi ngoài `scripts/perf`: `shell.qml` (6 dòng), `qml/components/PageHost.qml` (6),
  `qml/services/Heartbeat.qml` (+52), `qml/services/qmldir` (+1), `config/architecture.json`
  (41); tổng +102/−4. `AGENTS.md` không khác main; mode của `config/architecture.json` là 100644
  như main.

## 8. Git và máy

- **lme-fedora-niri-qs**: `origin/perf/responsive-v2` = `a7df45c` (push `b990406..a7df45c`).
  Checkout harness trên host `~/.cache/lme-perf/rv2/repo` ở `a7df45c`, sạch. Shell
  deployed `~/lme-fedora-niri-qs` ở `8374e94` (main), sạch, đang chạy (pid sau run cuối cùng
  1223686).
- **Archive repo** (`GLM-sessions-sandbox-archive`), branch `session/2026-11-27-eyes`: phần 2 của
  phiên nằm trong commit ngay sau `6516fa0`: `sessions/2026-11-27-eyes/` (STATUS.md,
  EYES-ANALYSIS.md, PR-DRAFT.md, `s1s3/` gồm AB-S1S3-COMPARE, AB-S2-COMPARE, S1-B2-EYES-CHECK,
  các PEEK-*, `summaries/` = summary.md của 6 run) và `tools/lme-eyes/` (29 script). Clone trong
  sandbox `work/archive` có sẵn 38 file khác chỉ khác mode (100644 → 100755) từ trước — không
  đụng tới, không commit.
- **Host lúc 13:28**: không còn tiến trình perf hay stand-in; 1 cửa sổ (helium, workspace id 1,
  idx 1); workspace đang focus id 6 (idx 2) trống; **có thêm workspace id 7 (idx 3)** xuất hiện
  sau 13:05 — các run A ghi workspace trước/sau đều là (6, 2) và bước workspace bị skip, không
  xác định được ai tạo (có thể là owner).

## 9. Việc tiếp theo (chờ owner quyết)

1. Đọc `PR-DRAFT.md`: mở một PR cả nhánh, hay tách PR chỉ shell (`33b204d` + `7fc1df9`) và PR
   harness riêng.
2. Có cần chạy N ≥ 10 mỗi phía cho S1/S3 trước khi kết luận về S1 không (lệnh ở mục 10).
3. Quyết định mục 6.1 (cadence của burst `aba`).
4. Sau đó: profilé stall dựng page (mục 6.2), cơ chế nuốt click của Settings (6.3), Escape thứ hai
   ở các panel khác (6.4).

## 10. Lệnh dùng lại (host)

- Chạy một loạt S1/S3 (mỗi đối số `MODE:TREE:LABEL`, MODE ∈ `s1eyes` | `s3` | `fast`):
  `python3 scripts/host_run.py "bash /tmp/vis_batch.sh s1eyes:/home/kimhoanglong/.cache/lme-perf/rv2/p-main:<label> ... 2>&1" --timeout 560`
  (script nằm ở `/tmp/vis_batch.sh`, `/tmp/vis_run_s1s3.sh` trên host — mất nếu reboot; bản sao
  `scripts/` và `eyes-analysis/tools/`). Không chạy việc nặng trên host khi đang đo.
- Fetch: `python3 -I scripts/fetch_s1s3.py <label> ...` (run mới nhất theo label, kèm `eyes/`).
- Xem: `python3 -I scripts/s1s3_peek.py <run dir>`; bảng A vs B:
  `python3 -I scripts/s1s3_ab_compare.py A:<label> ... B:<label> ... [--out FILE]`;
  kiểm click bằng ảnh: `python3 -I scripts/eyes_tabs_check.py <run dir>`;
  khoảng click burst S2: `python3 -I scripts/s2_burst_gaps.py <run dir>`;
  đầu run (tree, probe, khôi phục): `python3 -I scripts/run_headers.py <run dir>`; số lần đọc
  rect trước khi click (S1): `python3 -I scripts/still_reads_check.py <run dir>`.
- Trace probe: `python3 -I scripts/probe_trace.py <run dir> <t0 epoch ms> <t1 epoch ms>`.
- Prepare lại tree (khi `probe_patch.py` đổi):
  `cd ~/.cache/lme-perf/rv2/repo/scripts/perf && python3 prepare.py --repo ~/.cache/lme-perf/rv2/repo --ref 8374e946beefe50022b0ac672580e587fd1691ed --out ~/.cache/lme-perf/rv2/p-main --diagnostics 7fc1df9 --force`
  (p-head: `--ref 33c687c48678d543a646ceb7774a6e3b6e5a5123 --out ~/.cache/lme-perf/rv2/p-head --force`).
  Tree chứa scripts cũ: luôn chạy từ repo checkout và truyền `--tree <tree>`.

## 11. Files phiên này (sandbox, `download/perf-responsive-v2/`)

- `PR-DRAFT.md`, `STATUS.md` (file này).
- `eyes-analysis/AB-S1S3-COMPARE.txt`, `S1-B2-EYES-CHECK.txt`, `S1FAST-B2-PEEK.txt`,
  `S3-B2-PEEK.txt`, `PEEK-s1-a.txt`, `PEEK-s3-a.txt`, `PEEK-s1fast-a.txt`, `AB-S2-COMPARE.txt`,
  `EYES-ANALYSIS.md`, `tools/` (29 file).
- `runs/s1-a/`, `runs/s3-a/`, `runs/s1fast-a/` (mỗi cái kèm `.tgz`; `s1-a/eyes/` 54 ảnh),
  `runs/s1-b2/`, `runs/s3-b2/`, `runs/s1fast-b2/`, `runs/s2-aside-a/`, `runs/s2-vision2/`.
