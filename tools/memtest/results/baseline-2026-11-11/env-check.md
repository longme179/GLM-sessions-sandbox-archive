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

- [x] cargo + rustc version
- [x] pnpm + tauri CLI (đã từng build v1.9.3)
- [x] Xvfb (cho GUI headless + C4 spike sau này)
- [x] build release minewrapd + minewrap-tauri từ source @ bfde421
- [x] chạy `run_baseline.sh` → `results/baseline-v1.9.3.md`

### Kết quả env-check A2 (2026-11-11)

| Mục | Kết quả |
|---|---|
| rustc | `rustc 1.99.1 (58cf8f9c3 2026-10-13) (Fedora 1.99.1-2.fc44)` |
| cargo | `cargo 1.99.1 (5f94df478 2026-08-27) (Fedora 1.99.1-2.fc44)` |
| pnpm | `12.18.0` |
| node | `v22.23.1` |
| tauri CLI | `tauri-cli 2.12.4` (`pnpm tauri --version` trong `ui/`) |
| Xvfb | **không cài** (`command -v Xvfb` rỗng → nhánh Wayland được dùng, xem dưới) |
| Session | `XDG_SESSION_TYPE=wayland WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/1000` |
| Ports 8081–8085 | trống (free) |
| CPU / RAM | 12 lõi / 15.156 MiB total (~6.8 GiB available lúc check) |
| pkg-config GUI deps | `webkit2gtk-4.1 2.54.2`, `libsoup-3.0 3.6.6`, `gtk+-3.0 3.24.52` — đủ để build GUI |
| Build daemon | `cargo build --release -p minewrapd` — **OK, 1m09.82s**, 5.863.312 B (5.59 MiB) |
| Build GUI | UI `pnpm install` + `pnpm run build` OK (0m01.07s); `cargo build --release -p minewrap-tauri` — **OK, 2m51.05s**, 10.889.464 B (10.39 MiB). Lần đầu fail vì thiếu sidecar `externalBin`; đã copy `target/release/minewrapd` → `src-tauri/binaries/minewrapd-x86_64-unknown-linux-gnu` (artifact build, không commit) rồi build lại OK |
| Harness verify | `sha256sum -c MANIFEST` — 16/16 OK |

**Cách chạy GUI:** dùng trực tiếp Wayland (`WAYLAND_DISPLAY=wayland-1`), KHÔNG dùng Xvfb (Xvfb không có trong máy).
