# perf/responsive-v2 — STATUS (hand-off, 2026-11-27 ~05:15, phiên 5)

Tiếng Việt (tóm tắt): phiên 5 trả lời trực tiếp yêu cầu của owner ("chụp ảnh màn
hình xem chuột có click trượt không"). **Đáp án: click KHÔNG TRƯỢT** — 54 click
đều vào tâm delegate (rect dy=0px), 6/17 click bị nuốt thậm chí có button render
đầy đủ 47px ngay dưới crosshair. VLM hallucinate 2 lần → phán quyết bằng pixel +
rect data. Công cụ "mắt" (eyes.py, run.py --eyes) đã commit + push (11bdbcd,
9a81fbd). S2 A-side (p-main) chưa chạy xong: run thử Skip ("Settings lists 0
page(s)") + cầu host (opentunnel) đứt SSL từ ~04:40. Máy sạch, shell deployed
chạy bình thường (restore OK cả 3 run).

## Câu hỏi của owner và câu trả lời (bằng chứng hình ảnh)

Owner quan sát realtime thấy "click trượt hoặc cuộn lố". Kết quả điều tra:

1. **grim trên niri KHÔNG chụp hardware cursor** (park 3 vị trí, diff pixel = 0
   quanh mọi điểm park) → mắt làm khác: eyes.py vẽ crosshair đỏ tại tọa độ click
   (harness biết chính xác) vào ảnh grim, crop 440x440, JPG + manifest.
   `run.py --eyes` bật (mặc định tắt — run đo đạc không đổi).
2. Chạy thật: **s2-vision2** trên p-head, warmup 1 + s2 all × 3 reps = 54 click,
   67 ảnh (run 20261127-041443-s2-vision2). ok 11/18, 13/18, 13/18 — khớp đêm 4.
3. **Rect data (nav_trace)**: cả 17 click FAIL đều tâm delegate, dy=0px, cách mép
   24-25px (delegate 182x48). Không click nào ngoài nút. → KHÔNG TRƯỢT.
4. **Pixel (gradient theo hàng trong ảnh)**: 6/17 FAIL (keybinds ×3, behavior ×3)
   có hàng button 47px render đầy đủ đúng dưới crosshair — nút hiện đầy đủ, click
   vào tâm, shell im lặng. Các FAIL còn lại tại vùng fold (rect có thể stale sau
   scroll).
5. **Pattern xác định theo vị trí scroll** (không ngẫu nhiên): rep1 == rep2
   (luminance giống từng byte): đầu list (elements→topbar) + cuối list (keybinds,
   behavior) FAIL; giữa OK. rep0 (list đứng giữa): nightLight, notifications+
   clipboard, keybinds+lock, behavior+about FAIL. Lặp chính xác giữa reps → hành
   vi xác định của shell, cùng họ với S2 (nghi state machine navigation/recede
   nuốt input).
6. **VLM: 2 batch, 2 lần hallucinate** (đảo nhãn OK/FAIL, nói ảnh OK là fail;
   mâu thuẫn rect data). Khớp bài học 28 trong archive. Quy tắc: VLM không dùng
   làm phán quyết, chỉ mô tả kèm kiểm chứng chéo.

## Bug harness phiên 5 (đã khắc phục — nhớ cho session sau)

- **Tree p-head chứa scripts cũ 33c687c** (không grid sweep, không
  settled_point/nav_trace). Session 3-4 thực ra chạy scripts từ repo checkout
  (~/.cache/lme-perf/rv2/repo, e5ef1b1); tree chỉ cung cấp QML. Chạy run.py từ
  tree → calibrate Skip (đây là lý do s2-vision1 Skip). **LUÔN chạy từ repo
  checkout.**
- PTY bridge: lệnh một dòng dài (base64 cả script > ~10KB) làm treo PTY.
  host_push.py đẩy file theo chunk 3KB qua nhiều lệnh ngắn (an toàn).
- p-main export cũ: SettingsView có `settingsHover = this` (Item, không có
  .point) → pointer read throw. Đã sed thành `pointerWatch` (giống p-head),
  preflight 208 files OK.

## S2 A-side (p-main) — CHƯA XONG, đã chuẩn bị sẵn

- Run 20261127-043450-s2-aside-a Skip: "Settings lists 0 page(s)". Probe p-main
  đọc `SettingsRegistry.pages.map(...)` (không có helper probePages như p-head);
  khi FeatureCatalog chưa settle → pages rỗng → settings_ready trả với 0 pages.
  Session sau: xem timing (đợi FeatureCatalog.ready / settings.ready mark) rồi
  chạy lại `s2:variants=all,reps=3` + --eyes trên p-main, so tỉ lệ nuốt A vs B
  → trả lời regression hay pre-existing.
- Script chạy sẵn: download/perf-responsive-v2/eyes-analysis/tools/
  vis_run_s2aside.sh (chạy từ repo checkout).

## Cầu host đứt (lý do dừng)

Từ ~04:40 giờ host: mọi lệnh host_run.py fail `SSL: UNEXPECTED_EOF_WHILE_
READING` (opentunnel). Retry 3 lần trong ~4 phút, không hồi. Kiểm tra tunnel ở
session sau; nếu vẫn đứt, owner cần restart tunnel.

## Git state

- **lme-fedora-niri-qs**: origin/perf/responsive-v2 = `9a81fbd` (phiên 5 push:
  11bdbcd eyes.py + installer, 9a81fbd wiring run.py/scenarios.py). Repo checkout
  trên host detached HEAD 9a81fbd, working tree có patch eyes đã commit sạch.
- **GLM-sessions-sandbox-archive**: branch `session/2026-11-27-eyes` đã push
  (sessions/2026-11-27-eyes/EYES-ANALYSIS.md + tools/lme-eyes/). LƯU Ý: PAT thứ hai
  trong upload/working-protocol.txt đã OLD (401 Bad credentials); token owner gửi
  trực tiếp trong tin nhắn 2026-11-26 mới dùng được → scripts/archive_cred3.sh.

## Còn lại (ưu tiên session sau)

1. S2 A-side (p-main): sửa timing settings_ready trên tree cũ → 3 reps + eyes →
   so A vs B (regression?).
2. S1 CC tabs A/B, S3 mixed ≥3 reps.
3. PR prep: revert 4469385 (AGENTS.md), check.sh, PR text. Eyes commits đang nằm
   trên perf/responsive-v2 — cân nhắc tách riêng nếu PR chỉ nên chứa fix shell.

## Files phiên này (sandbox)

- download/perf-responsive-v2/runs/s2-vision2/ — records.json + eyes/ (67 ảnh)
- download/perf-responsive-v2/eyes-analysis/ — EYES-ANALYSIS.md (bằng chứng đầy
  đủ), cursor-probe/ (thí nghiệm grim), tools/ (12 script: mắt, push, chạy, phân
  tích pixel/rect/dim)
- Trên host: runs/20261127-034106-s2-vision1 (Skip), 20261127-041443-s2-vision2
  (thành công), 20261127-043450-s2-aside-a (Skip pages=0)
