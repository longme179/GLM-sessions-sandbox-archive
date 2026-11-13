# NHIỆM VỤ: P1 CHUNK 4 — Slint GUI: Nodes (multi-node) — port NodeService + Nodes UI (Minewrap)

> DRAFT — dispatch SAU khi P1-C3 collected + verified. Cập nhật commit
> hash, baseline test count, PSS trước khi gửi.

Bạn là agent tự chủ coding trên máy Fedora 44 (12 lõi, niri Wayland) của user.
Làm TOÀN BỘ task dưới đây rồi báo cáo. KHÔNG hỏi giữa chừng — tự quyết chi
tiết kỹ thuật trong phạm vi spec; gì lệch spec thì ghi rõ trong report.
Mọi tuyên bố "done" phải kèm bằng chứng machine-verified (lệnh + output,
screenshot, số đo). Nghiêm cấm bịa số/kết quả.

## Bối cảnh

- Minewrap: Rust workspace (edition 2024, AGPL-3.0-only, `warning = deny`).
  main = P0 daemon-first + P1-C1/C2 (Slint GUI) + P1-C3 (Properties/Mods/
  Notifications tabs + theme tokens + BUG-D1 fix). GUI PSS ~20-23 MiB
  (budget < 60 MB). Tests baseline: <CẬP NHẬT SAU C3>.
- Working copy: `~/dev-memtest/build/Minewrap-p0`, branch `p1-c3` @
  <CẬP NHẬT> (hoặc main nếu đã merge). KHÔNG đụng worktree khác.
- Hiện GUI chỉ nói chuyện với daemon LOCAL (spawn tự động, URL + token
  từ daemon spawner). Chưa có khái niệm node từ xa trong GUI.
- Tài sản cũ để PORT: `src-tauri/src/node_service.rs` (554 LOC) — nodes.json
  (registry 0600, NodeRecord {id,name,url,token}), local node auto-tạo,
  RemoteClient per node, health poll, state cache, upsert 401-retry.
  `ui/src/components/Nodes.svelte` (180 LOC) — bảng nodes + form Add
  (name/url/token write-only) + Remove. TOKEN KHÔNG BAO GIỜ hiển thị lại
  sau khi nhập (chỉ lưu nodes.json).

## Bước 0 — Branch

```
cd ~/dev-memtest/build/Minewrap-p0
git fetch origin
git checkout -b p1-c4 origin/p1-c3   # hoặc origin/main nếu C3 đã merge
cargo check --workspace
```

## Bước 1 — Port NodeService vào crates/minewrap-gui (Rust, không Tauri)

- File mới `crates/minewrap-gui/src/nodes.rs` (+ modules phụ nếu cần):
  port logic `src-tauri/src/node_service.rs`: nodes.json path (XDG config
  dir của GUI — cùng quy tắc daemon spawner đang dùng), NodeRecord, local
  node entry (URL + token của daemon mình spawn), remote nodes, health
  poll định kỳ (dùng `RemoteClient::health_timeout` + `state_from_error`),
  state cache (NodeState enum từ minewrap-remote).
- Đọc `src-tauri/src/node_service.rs` TRỰC TIẾP trước khi port — giữ
  đúng semantics (0600, token không log, 401 refresh-retry).
- Runtime wiring: health poll chạy trong runtime thread (cùng pattern
  C1-C3, gửi kết quả về UI qua channel + timer drain); KHÔNG block UI.
- Local node: tích hợp với daemon auto-spawn hiện có (URL/token từ đó).

## Bước 2 — GUI: Nodes UI + sidebar multi-node

1. **Sidebar**: nhóm theo node — heading tên node (local: "Local"; remote:
   tên user đặt) + state dot (online/offline/...); instances của node đó
   lồng dưới. Chọn node → hiện instances; giữ hành vi chọn instance
   hiện có (console/settings/properties/mods/notifications đều hoạt động
   với instance của node ĐANG CHỌN — mọi call REST phải qua client của
   node đúng).
2. **Panel Nodes** (tab mới hoặc nút cạnh "Add instance"): bảng nodes
   (name, url, state) + form Add (name, url, token write-only) + Remove
   (confirm inline row; local node KHÔNG removable). Sau add: health
   check ngay → state hiện trong bảng.
3. WS events + console: mỗi node một connection? — C3 hiện có 1 daemon.
   Scope: console WS + events WS vẫn CHỈ cho node của instance đang chọn
   (connect khi chọn, disconnect khi đổi) — đơn giản và đủ. Ghi rõ trong
   report nếu làm khác.

## Bước 3 — Test

- Unit: nodes.json load/save round-trip (file 0600), NodeRecord CRUD,
  state_from_error mapping, local-node upsert.
- `cargo test --workspace` bare (25565 free) — baseline phải pass.
- Integration giả lập: 2 daemon trên 2 port (8390 local + 8391 remote,
  data riêng như G3 round-2 đã làm: g3r2-node2) → GUI thấy cả 2, instance
  của remote node start/stop được (E2E Bước 4).

## Bước 4 — Build + visual verify (display thật, CÓ GUARD)

[MÁY: click_abs / wtype -k test đầu việc / click_multi / wheel /
KHÔNG đọc ảnh vào context — 422 / pgrep -x / GUARD pgrep + niri windows]

1. `cargo build --release -p minewrap-gui --no-default-features` (+ default).
2. Scratch: daemon A port 8390 (data p1c4-data, XDG p1c4-xdg, instance
   p1c4stub, fakejava-echo, SLP 25590); daemon B port 8391 (data
   p1c4-node2-data, XDG p1c4-node2-xdg, instance p1c4r2stub, SLP 25591).
   GUI trỏ A làm local; thêm B qua form Add (URL http://127.0.0.1:8391,
   token của B).
3. E2E (focus → act → grim → REST đối chiếu):
   - S1: sidebar hiện 2 nhóm node; local online; remote online sau add.
   - S2: chọn instance của remote node → console live (gõ command qua
     REST của daemon B → dòng xuất hiện).
   - S3: start/stop instance remote (nút Start → daemon B spawn fakejava).
   - S4: Remove remote node → nhóm biến mất; daemon B còn sống (không bị
     dính); local node KHÔNG có nút Remove.
   - S5: disconnect path: kill daemon B (đúng PID) → state node B →
     offline/... (như G3 #23 pattern); relaunch B → GUI reconnect health.
   Ảnh: `~/dev-memtest/results/p1-c4/shot-s1..s5.png`.
4. PSS: 3×60 s idle (2 nodes) + 1×60 s console remote mở, memsample.py,
   pgrep -x minewrap-gui.

## Bước 5 — Commit + push + dọn + report

- Commit `[P1-C4]`; push origin p1-c4. Dọn máy (kill đúng PID: GUI,
  daemon 8390/8391, fakejava, SLP stubs; /proc/<pid>/cmdline; không
  pkill -f; git status sạch; XDG scratch + data dirs giữ nguyên cho
  GLM verify sau).
- `~/dev-memtest/results/p1-c4/REPORT.md`: trạng thái từng mục, bảng
  PSS, LOC, commits, deviations. Tin nhắn cuối ≥300 ký tự.

## Ràng buộc chung

- Repo sạch (Q8): KHÔNG commit tool/screenshot/kết quả.
- KHÔNG sửa `src-tauri/`, `ui/` (chỉ ĐỌC làm tham chiếu port); crate
  khác ngoài minewrap-gui: tách commit + giải thích.
- App thật của user: không đụng.
