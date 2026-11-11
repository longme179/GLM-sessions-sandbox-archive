# env-check — A3: môi trường build & xác minh harness (2026-11-11)

## Sandbox GLM (Debian 13, 2 lõi, 4 GB — không phải máy đo baseline)

| Mục | Kết quả |
|---|---|
| Rust toolchain | `rustc 1.99.1 (58cf8f9c3 2026-10-13)` / `cargo 1.99.1` — cài qua rustup (profile minimal) |
| Build daemon | `cargo build --release -p minewrapd` — **OK, 1m47s**, binary 5.58 MiB (5.849.600 B) |
| Test headless | `cargo test -p minewrap-core -p minewrapd -p minewrap-remote` — **47/47 pass** (core 45 + daemon 2 + remote 0), 0 failed |
| Build GUI | **Không thể** — sandbox không có sudo → không cài được `libwebkit2gtk-4.1-dev`/`libsoup-3.0-dev`. Theo R7 (plan v1.1): GUI build qua agent trên máy user, patch base64 byte-exact từ GLM |
| Harness verify | Toàn tuyến `run_baseline.sh` chạy OK với minewrapd thật: S0/S1/S3/SR/SW/SW2 + GUI-tree (GUI giả để test logic cây). Artifacts: `results/sandbox-verify/` |

### Số đo sandbox (CHỈ để xác minh cơ chế — KHÔNG phải baseline)

Sandbox 2 lõi → tokio worker = 2 → threads 3 (máy user 12 lõi → 13 như báo cáo).
RSS/PSS lệch báo cáo ~+0.3–0.9 MiB do khác distro/libc/build — đúng như dự kiến,
ngưỡng §15.4 chỉ áp dụng khi đo lại trên máy user (A2).

| Kịch bản | RSS | PSS | threads |
|---|---|---|---|
| S0 | 5.49 | 3.58 | 3 |
| S1 | 6.25 | 4.43 | 3 |
| S3 | 7.08 | 5.18 | 3 |
| SR | 6.99 | 4.99 | 3 |
| SW | 7.47 | 5.57 | 3 (WS: 29 msg / 28 log events / 46.8 KB) |
| SW2 | 5.73 | 3.76 | 3 |

### Phát hiện mới trong lúc verify harness (ghi nhận cho Phase B)

**GapF — daemon panic khi spawn fail**: `Control::Start` với `spawn_server` lỗi
(java_path sai / work_dir thiếu) → `process.rs:433` gọi
`transition(Crashed, "spawn_failed")` từ state `Offline` → `assert!` ở
`process.rs:368` **panic** `'invalid transition Offline -> Crashed'` → owner
task chết, instance đứng im không phản hồi control nữa (daemon vẫn sống).
Bằng chứng: `results/sandbox-verify/` log SR-smoke trước khi fix symlink.
→ Nên xử lý trong B1/B5 (state keeper + graceful shutdown) kèm unit test.

**Xác nhận runtime GapB**: sau khi stub online (Done line + stream 0.5 s),
`GET /api/v1/instances/{id}` vẫn trả `combined_state: "offline"` — snapshot
REST của daemon v1.9.3 không bao giờ được cập nhật (0 caller update_process).
Harness đã ghi nhận trường này vào JSON kết quả (`rest_combined_state_after_start`).

### Ghi chú kỹ thuật harness (bài học khi port)

- Config TOML: đường dẫn tương đối resolve theo **thư mục chứa file config**
  (`config.rs resolve_paths`), KHÔNG theo cwd daemon → configs dùng `../work/...`.
- `java_path "./fakejava"` resolve theo **cwd của process server (= work_dir)**
  → harness symlink stub vào mỗi work_dir (`ensure_stub_links`).
- `/logs` trả LogBuffer (seq tăng theo stream) — dùng làm tín hiệu "online"
  thay vì REST state (stale do GapB).

## Máy user (Fedora 44, 12 lõi — máy đo baseline) — agent xác nhận trong A2

- [ ] cargo + rustc version
- [ ] pnpm + tauri CLI (đã từng build v1.9.3)
- [ ] Xvfb (cho GUI headless + C4 spike sau này)
- [ ] build release minewrapd + minewrap-tauri từ source @ bfde421
- [ ] chạy `run_baseline.sh` → `results/baseline-v1.9.3.md`
