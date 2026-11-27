# Eyes analysis — s2-vision2 (p-head, 2026-11-27 04:14, run 20261127-041443-s2-vision2)

## Câu hỏi của owner

"Tôi có quan sát script của bạn làm việc in realtime và thấy có vẻ bạn click trượt,
hoặc cuộn lố qua. có thể bạn thử chụp ảnh màn hình rồi dùng VLM để xem con chuột thử."

## Nền tảng kỹ thuật (đã thí nghiệm)

1. **grim trên niri KHÔNG chụp con trỏ.** Park chuột tại 3 vị trí (300,300),
   (1500,300), (960,540) — diff pixel giữa các cặp ảnh: 0% thay đổi quanh điểm park.
   VLM xác nhận: không thấy cursor trong crop nào.
2. Do đó "đôi mắt" làm khác: harness biết chính xác tọa độ nó click →
   `eyes.py`: grim → vẽ crosshair đỏ tại điểm click → crop 440x440 → JPG + JSON
   sidecar + manifest. Cờ `--eyes` của run.py bật; mặc định tắt (run đo đạc
   không đổi). Commit `11bdbcd` + `9a81fbd`, đã push lên origin/perf/responsive-v2.

## Chạy thật: s2-vision2 (p-head, warmup 1 vòng + s2 all × 3 reps, 54 click, 67 ảnh)

Lưu ý harness: run từ **repo checkout e5ef1b1** (scripts mới), tree p-head chỉ là
QML. Tree p-head chứa scripts bản cũ 33c687c — chạy từ đó sẽ Skip calibrate
(không có grid sweep). Đây cũng là lý do run s2-vision1 đầu tiên Skip.

### Kết quả click (54 click, variant "all", 3 reps)

- ok 11/18 (rep0), 13/18 (rep1, rep2) — khớp các run đêm trước (11-13/18).
- 17 click FAIL (không navigate). Tất cả retry flags theo fix fffc66a.

### Bằng chứng 1 — rect probe (nav_trace): click KHÔNG trượt

Cả 17 click FAIL đều nằm **chính xác tâm delegate** (dy=0px, cách mép 24-25px,
delegate 182x48). Không có click nào ngoài nút. 37 click OK: inside=37, outside=0.

### Bằng chứng 2 — pixel (đọc từ ảnh eyes): button có thật ở đó

Phân tích gradient độ sáng từng dòng ảnh quanh crosshair: 6/17 click FAIL
(keybinds ×3, behavior ×3) có **hàng button render đầy đủ 47px** nằm đúng dưới
crosshair — nút hiện đầy đủ, click vào tâm, shell vẫn không navigate.
Các FAIL còn lại nằm tại vùng fold/caption (rect nói delegate ở đó nhưng pixel
cho thấy nội dung khác — rect có thể stale sau scroll).

### Bằng chứng 3 — pattern FAIL theo vị trí scroll (không ngẫu nhiên)

- rep1, rep2 (giống nhau từng byte luminance): elements→topbar (đầu list) FAIL,
  keybinds, behavior (cuối list) FAIL. Control: controlLayout→weather OK.
- rep0 (list đứng giữa): nightLight, notifications+clipboard, keybinds+lock,
  behavior+about FAIL.
- Kết luận: các entry bị nuốt phụ thuộc **vị trí trong list sau scroll**, lặp lại
  chính xác giữa các rep → hành vi xác định của shell, không phải nhiễu harness.

### VLM: 2 lần gọi, 2 lần hallucinate

- Batch 1 (ảnh 440px): VLM nói click FAIL "nằm dưới caption, dead space" — mâu thuẫn
  rect data (tâm delegate, dy=0). VLM còn đổi nhãn OK/FAIL.
- Batch 2 (crop sát 220px + context): VLM tiếp tục đảo nhãn (bảo ảnh OK là fail).
- Kết luận (khớp bài học 28 trong archive): VLM không dùng cho phán quyết; pixel +
  rect data là nguồn chuẩn. VLM chỉ có thể dùng để mô tả, luôn cần kiểm chứng chéo.

## Kết luận cho owner

Quan sát "click trượt / cuộn lố" khi xem realtime **không phải lỗi harness**:
mọi click đều vào tâm delegate đã settle; button được render đầy đủ tại điểm click
trong 6/17 trường hợp bị nuốt. Đây là hành vi thật của shell (đã xác nhận từ đêm 4
với retry cũng bị nuốt) — và nay có bằng chứng hình ảnh: **click chuẩn xác vào nút
hiện đầy đủ mà shell không phản ứng**. Giống triệu chứng S2 (trang đứng dim giữa
animation) — nghi ngờ cùng cơ chế: navigation/recede state machine nuốt input.

## Còn lại (ghi lúc cuối phiên 5 — cả ba mục dưới đây đã xong trong phiên 6, xem mục "Cập nhật phiên 6")

- S2 A-side (p-main): cần chạy để trả lời regression hay pre-existing.
  Đã chuẩn bị: settingsHover fix cho p-main (preflight 208 files OK).
  Run thử đầu Skip: "Settings lists 0 page(s)" — probe p-main đọc
  `SettingsRegistry.pages.map(...)` trả rỗng khi FeatureCatalog chưa settle;
  cần xem lại timing settings_ready trên tree cũ (settings.ready mark có thể
  khác), rồi chạy lại.
- S1 CC tabs A/B, S3 mixed ≥3 reps.
- PR prep: revert 4469385 (AGENTS.md), check.sh, PR text.

## Files

- `../runs/s2-vision2/eyes/` — 67 ảnh + manifest.json (mỗi click 1 ảnh crop
  crosshair; shot = thời điểm click).
- `../runs/s2-vision2/records.json` — records + meta (nav_trace đầy đủ).
- `cursor-probe/` — thí nghiệm grim-cursor (park 3 vị trí, diff = 0).
- Trên host: `~/.cache/lme-perf/rv2/runs/20261127-041443-s2-vision2/` (đầy đủ),
  repo checkout ở 9a81fbd (detached, đã push origin/perf/responsive-v2).

## Cập nhật phiên 6 (2026-11-27, 11:00–13:35 giờ host)

### S2 phía A (main): hành vi có sẵn, không phải regression

Run A `20261127-111001-s2-aside-a` (p-main) so với run B `20261127-041443-s2-vision2` ở trên,
cùng variant `all`, 3 rep: A 16/54 và B 17/54 click không navigate; 16 cặp (rep, page) trùng
nhau, B chỉ có thêm `about` ở rep0 (`AB-S2-COMPARE.txt`). 67 ảnh mỗi phía, 54/54 click khớp với
một ảnh.

### S1 Control Center: vì sao phiên trước nhìn thấy "click trượt"

- Run 11:22 (`runs/s1s3-b/`, **không hợp lệ**): harness cũ click 127 ms sau khi mở panel, khi
  panel stage còn đang trượt vào (transitioning hết ~1.48 s). Trace cho thấy `panel[4]` (transitioning)
  true ở +22 ms và chỉ false ở +1484 ms. Run đó có 11 click "mù" ra desktop trống.
- Đã sửa harness (`c2e51ba`, `08da4b7`, `b990406`): S1 đợi stage đứng yên rồi mới đọc rect;
  mỗi rep lưu rect của từng nút tab (`meta.s1_tab_rects`).
- Chạy lại có mắt, mỗi phía một run S1: B `20261127-122409-s1-b2`, A `20261127-130005-s1-a`.
  36 lần đọc rect mỗi run, tất cả chỉ cần 2 lần đọc (moved 0.0 px) → khi đọc thì stage đã đứng yên.
- Ảnh: 54 crop mỗi phía (ordered 3 rep × 6 tab = 18 click, random 3 rep × 12 = 36), crop 440 px
  quanh điểm click, crosshair đỏ tại điểm click.

### Kiểm ảnh S1 bằng hình học (không dùng VLM)

- Hai file kết quả: `S1-B2-EYES-CHECK.txt` (phía B) và mục "Eyes" của
  `AB-S1S3-COMPARE.txt` (A và B).
- Kết quả: **54/54 mỗi phía** điểm click nằm trong rect nút tab mà harness đọc được; nút
  287–288 × 40 px, tâm (px cửa sổ) x 1163.5 / 1456 / 1748.5, y 212 / 257; lề trái/phải 143–144 px,
  trên/dưới 20 px → đúng tâm nút. Hình học hai phía giống hệt nhau.
- Bằng chứng hành vi khớp: mỗi click sinh `cc.select <tab>` đúng tab sau 9–16 ms khi GUI thread
  rảnh (click → built/present).
- Phép thử "đo màu chạy từ tâm ra mép nút" trên crop **không kết luận được**: chữ nhãn của nút
  nằm ngay dưới crosshair nên màu đổi sau ~29–44 px, chưa tới mép nút. Không dùng làm bằng chứng.
- Công cụ: `tools/eyes_tabs_check.py <run dir>`.

### A (main) so với B (nhánh) — cùng harness, probe `6fc853ea329a`

- S1: không khác. Click → built 9–16 ms, click → settled 385–403 ms (trừ `notifications` trên
  nhánh: 518 ms), Escape → gone 20–24 ms, 6/6 rep ok mỗi phía. Stall GUI thread > 100 ms trong 9
  rep: main 13 (tệ nhất 2215 ms), nhánh 9 (tệ nhất 3088 ms).
- S3: chỉ khác ở `activity`. Trên main 0/9 bước `activity` đóng bằng Escape (9 lần + 3 lần warm-up
  phải đóng qua IPC); trên nhánh 9/9 (median 16.7 ms, max 451.6 ms). Các panel khác: mở 104–304 ms
  median, Escape → gone 17–49 ms (settings, cửa sổ riêng: 91 / 236 ms), như nhau hai phía.
- Chi tiết: `AB-S1S3-COMPARE.txt`, `S3-B2-PEEK.txt`, `S1FAST-B2-PEEK.txt`, `PEEK-s1-a.txt`,
  `PEEK-s3-a.txt`, `PEEK-s1fast-a.txt`.
- Lưu ý: mỗi phía 3 rep cho mỗi variant — dưới luật N ≥ 10 của harness, chỉ mang tính chỉ dấu.

## Files (phiên 6)

- `AB-S2-COMPARE.txt`, `AB-S1S3-COMPARE.txt`, `S1-B2-EYES-CHECK.txt`, `S1FAST-B2-PEEK.txt`,
  `S3-B2-PEEK.txt`, `PEEK-s1-a.txt`, `PEEK-s3-a.txt`, `PEEK-s1fast-a.txt`.
- `tools/` — 29 script (chạy, fetch, peek, so sánh, kiểm ảnh, vá repo có neo).
- Ảnh và records: `../runs/s1-b2/eyes/` (54 ảnh), `../runs/s1-a/eyes/` (54 ảnh), `../runs/s3-b2/`,
  `../runs/s1fast-b2/`, `../runs/s3-a/`, `../runs/s1fast-a/`.
- Hand-off: `../STATUS.md`; bản PR: `../PR-DRAFT.md`.
