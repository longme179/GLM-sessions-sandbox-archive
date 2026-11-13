# Minewrap — Toolkit spike SPEC (C0) + Measurement protocol (C4)

> Đợt 1 Phase C · 2026-11-11 · Phụ lục của `plans/2026-11-11-minewrap-p0-spike-plan.md` (§6).
> Viết bởi GLM; agent (`opencode/deepseek-v4.1-flash-free`) thực thi trên máy user;
> GLM review diff verbatim + tái đo ngẫu nhiên ≥1 kịch bản/toolkit.
> **Q8 (bắt buộc):** toàn bộ code spike + kết quả đo nằm ngoài repo Minewrap —
> working copy `~/dev-memtest/spikes/{slint,iced,gtk4}/`, master ở archive repo
> `spikes/2026-11-toolkit/`. KHÔNG commit/push gì vào repo Minewrap.

## C0 — Mini-app chung (một app, ba toolkit)

Một app duy nhất, replicate đúng "hình thù" Minewrap hôm nay để đo đúng cái
sẽ phải chịu sau khi port (P1):

- **Cửa sổ:** 1280×800, dark theme, màu token lấy từ
  `~/dev-memtest/build/Minewrap/ui/src/styles/tokens.css` (repo v1.9.3 @
  `bfde421` đã clone từ A2; nếu thiếu thì clone lại). Không dùng màu hệ.
- **Sidebar trái (220 px):** 5 instance giả (tên + badge trạng thái:
  online / offline / crashed / unresponsive — trạng thái ban đầu:
  1 online, 2 offline, 1 crashed, 1 unresponsive). Footer sidebar: trạng
  thái node ("local · connected").
- **Console (phần chính):** ring **đúng 1000 dòng** FIFO; mỗi dòng
  `[HH:MM:SS] [LEVEL] message`; LEVEL: INFO (mặc định), WARN (vàng),
  ERROR (đỏ), DEBUG (xanh) — tỉ lệ ~60/20/15/5; **bôi đen chọn + Ctrl+C
  copy được** (native text selection — HARD REQUIREMENT Q3: nếu toolkit
  không có sẵn, thử biến thể gần nhất và GHI KẾT QUẢ THẬT, không bịa);
  auto-scroll stick-to-bottom, ngắt stick khi user kéo lên (nút/ hành vi
  "jump to latest" khi đã rời bottom); chịu **burst 2000 dòng < 1 s**
  không khựng UI (nạp theo batch, không re-render toàn list).
- **Form dưới console:** 2 text input + 1 select (4 option) + 1 button
  Apply — đổi tên instance đang chọn trong sidebar (chứng minh state
  two-way binding).
- **Status bar đáy:** trạng thái + giờ + số dòng đang có trong ring.
- **Generator dữ liệu (in-process, không network):** nút "Burst 2000",
  toggle "Stream 2 dòng/s", nút "Clear"; **CLI `--auto`** cho đo tự động:
  sau 10 s tự burst 2000 dòng, sau đó stream 2 dòng/s trong 60 s, rồi
  exit (in ra stderr timestamp "ready" khi event-loop vẽ frame đầu).
- **Font:** Noto Sans 10 pt cả 3 app (fontconfig chung) — loại trừ biến
  số font giữa các toolkit.

## Biến thể từng toolkit

- **C1 Slint:** Slint 1.x, backend `winit-software`
  (`SLINT_BACKEND=winit-software`); tắt feature `renderer-femtovg`. Đo 2
  cấu hình: **default** (accessibility on) và **tuned** (tắt
  `accessibility`). Console: `ListView` + text select — nếu selection
  không có sẵn, thử mô hình "LineEdit readonly nhiều dòng" hoặc custom —
  ghi rõ kết quả thật.
- **C2 iced:** iced 0.13, renderer **tiny-skia** (CPU). Console: thử
  `text_editor` (có selection native) VÀ variant "dòng text có màu trong
  column" — nếu `text_editor` không tô màu per-line được thì ghi trade-off
  thật.
- **C3 gtk4-rs:** gtk4-rs 0.9: `TextView` trong `ScrolledWindow` +
  `TextTag` màu (selection native sẵn); renderer cairo (mặc định, không
  GPU). PSS là số thật trên máy đo (GTK4 kéo libgtk — đúng chủ đích đo).

## C4 — Protocol đo chuẩn

- **Hiển thị:** `Xvfb :99 -screen 0 1280x800x24` (đồng nhất, software
  path — đúng mục tiêu không GPU). A3 đã ghi máy user KHÔNG có Xvfb
  (Wayland direct): BƯỚC 0 phải xác nhận `command -v Xvfb`; nếu thiếu,
  thử `sudo dnf install -y xorg-x11-server-Xvfb`; nếu vẫn không có → đo
  trên session Wayland thật (WL_XDG_RUNTIME_DIR như A2 đã làm GUI) và
  GHI RÕ "environment: wayland-direct" trong mọi bảng (không so chéo
  Xvfb↔Wayland mà không chú thích). Xác nhận window mapped bằng
  `xwininfo` (Xvfb) hoặc `wlr-randr`/screenshot (Wayland); screenshot
  (`xwd`/`grim`) lưu làm bằng chứng.
- **Đo:** `~/dev-memtest/memsample.py` (A1) trên **cây process app**,
  1 Hz, cùng thuật toán baseline (smaps_rollup RSS/PSS/USS, loại subtree
  fakejava — không áp dụng ở đây vì không có subprocess, nhưng giữ nguyên
  sampler).
- **Kịch bản mỗi app:** (1) idle 60 s; (2) burst: đo 30 s quanh thời
  điểm burst 2000 dòng (tức `--auto` + canh giờ, hoặc trigger thủ công);
  (3) stream 2 dòng/s trong 60 s. **3 runs/kịch bản**, báo cáo
  **median [min–max]**.
- **Thêm:** cold-start (exec → frame đầu: instrument "ready" vào stderr
  + timestamp + xác nhận bằng screenshot); binary size (release, strip
  như workspace: `lto=true, codegen-units=1, strip=true`); build time
  (clean `cargo build --release`, ghi máy 12 lõi); LOC (cloc hoặc `wc -l`
  Rust + markup); danh sách dependency hệ thống (`ldd` top-level).
- **AC:** jitter run-to-run ≤ 0,15 MiB; số ghi kèm environment (kernel,
  display, font, locale). Mọi số chưa verify → ghi "unverified".

## Checklist nghiệm thu console (điền vào report từng toolkit)

| # | Yêu cầu | Đạt / Thiếu | Ghi chú |
|---|---|---|---|
| 1 | Ring đúng 1000 dòng FIFO | | |
| 2 | Màu per-level (INFO/WARN/ERROR/DEBUG) | | |
| 3 | Native selection + Ctrl+C copy | | |
| 4 | Auto-scroll stick + ngắt khi kéo lên | | |
| 5 | Burst 2000 dòng < 1 s không khựng | | |
| 6 | Form two-way (Apply đổi tên sidebar) | | |
| 7 | `--auto` chạy đủ 10s→burst→60s stream→exit | | |
| 8 | Font Noto Sans 10pt | | |

## Deliverables mỗi spike (GLM review qua diff verbatim)

1. Source hoàn chỉnh tại `~/dev-memtest/spikes/<toolkit>/` (Cargo project
   tự chứa, .gitignore target/).
2. `RESULTS.md`: bảng PSS/RSS/USS/threads — idle/burst/stream ×
   [min–max] median 3 runs; cold-start; binary; build time; LOC; ldd;
   checklist console trên; môi trường đo.
3. Screenshot bằng chứng (window mapped).
4. Ghi chú ergonomics + mức khó port 12 component Minewrap (subjective,
   đánh dấu rõ là nhận xét).

## License check (C5, GLM làm, agent không cần)

Minewrap = AGPL-3.0-only. iced & gtk4-rs = MIT (an toàn). **Slint =
GPLv3 / Royalty-Free / Commercial** — cần xác minh tương thích
GPLv3-code trong project AGPL-3.0-only + đọc kỹ Slint Royalty-Free
License terms trước khi chọn; escalate user nếu chưa yên tâm.
