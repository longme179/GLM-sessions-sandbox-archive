# NHIỆM VỤ: P1 CHUNK 5 — Packaging switch (AppImage = minewrap-gui) + retire src-tauri/ui (Minewrap)

> DRAFT — dispatch SAU khi P1-C4 collected + verified + user merge. Cập nhật
> commit hash + baseline test count trước khi gửi.

Bạn là agent tự chủ coding trên máy Fedora 44 (12 lõi, niri Wayland) của user.
Làm TOÀN BỘ task dưới đây rồi báo cáo. KHÔNG hỏi giữa chừng — tự quyết chi
tiết kỹ thuật trong phạm vi spec; gì lệch spec thì ghi rõ trong report.
Mọi tuyên bố "done" phải kèm bằng chứng machine-verified (lệnh + output,
screenshot + md5sum, số đo). Nghiêm cấm bịa số/kết quả.

## Bối cảnh

- Minewrap: Rust workspace (edition 2024, AGPL-3.0-only, `warning = deny`),
  origin/main @ <CẬP NHẬT SAU C4> = P0 daemon-first + P1-C1..C4 (Slint GUI
  đầy đủ tính năng: console/settings/properties/mods/notifications/nodes).
  GUI PSS ~20–23 MiB (budget < 60 MB). Tests baseline: <CẬP NHẬT SAU C4>.
- Working copy: `~/dev-memtest/build/Minewrap-p0`, branch `p1-c5` mới tạo
  off origin/main. KHÔNG đụng worktree khác.
- Vấn đề: repo vẫn mang DI SẢN HEAVY chưa dùng — `src-tauri/` (Tauri 2 shell,
  WebKitGTK, còn là workspace member) + `ui/` (Svelte 5 + pnpm) + các script
  build phụ thuộc chúng. GUI thật giờ là `crates/minewrap-gui` (Slint thuần).
- Daemon locator trong `crates/minewrap-gui/src/daemon.rs` (hàm
  `locate_daemon_binary`) đã hỗ trợ sẵn: `MINEWRAPD_BIN` env → cạnh GUI
  binary (`dir/minewrapd`) → `dir/binaries/minewrapd` → PATH. AppImage chỉ
  cần đặt `minewrapd` cạnh `minewrap-gui` trong `usr/bin/`.
- Icon: dùng icon hiện có (vd `src-tauri/icons/512x512.png` hoặc icon.png) —
  COPY sang `packaging/appimage/minewrap.png` TRƯỚC khi xóa src-tauri.

## Bước 0 — Branch

```
cd ~/dev-memtest/build/Minewrap-p0
git fetch origin
git checkout -b p1-c5 origin/main   # <hash>
cargo test --workspace 2>&1 | tail -3   # baseline phải pass trước khi bắt đầu
```

## Bước 1 — Packaging switch

1. `packaging/build-linux.sh` viết lại cho Slint AppImage:
   - Prerequisites chỉ còn: cargo + pkg-config các lib cần cho Slint
     (không webkit2gtk/libsoup/pnpm nữa — Slint software renderer không
     cần system GUI lib ngoài fontconfig/freetype mà cargo tự link).
   - Build: `cargo build --release -p minewrapd` +
     `cargo build --release -p minewrap-gui --no-default-features`
     (config đã đo PSS; accessibility OFF = RAM tối thiểu — đây là mục
     tiêu dự án; ghi chú trade-off trong script comment).
   - AppImage layout: `Minewrap.AppDir/usr/bin/minewrap-gui` +
     `usr/bin/minewrapd` (cạnh nhau — locator tự tìm thấy),
     `usr/share/applications/minewrap.desktop` (từ
     `packaging/appimage/minewrap.desktop`, sửa Exec=minewrap-gui),
     icon `usr/share/icons/...`. AppRun exec
     `usr/bin/minewrap-gui`. appimagetool fetch như cũ (tools/ local).
   - Vẫn ghi `dist/BUILD_FROM_SOURCE.md` (cập nhật lệnh mới — cargo only).
2. `build.sh` (build-from-source chính) cập nhật: GUI output =
   `target/release/minewrap-gui` (cargo, --no-default-features cho bản
   tuned; ghi rõ cả 2 mode). Bỏ nhánh pnpm/webkit deps. `--daemon-only`
   giữ nguyên. Xóa đoạn "AppImage bundling moves to P1" (đã tới lúc).
3. `packaging/minewrapd.service` giữ nguyên (headless path) — chỉ kiểm tra
   không tham chiếu gì đã xóa.

## Bước 2 — Retire src-tauri/ + ui/

1. `git rm -r src-tauri ui` (94 files). Root `Cargo.toml`: bỏ `src-tauri`
   khỏi members. `Cargo.lock` regenerate. `.gitignore`: bỏ mục pnpm/node.
2. Quét tham chiếu tồn (rg 'src-tauri|pnpm|svelte|tauri|webkit') trong
   README.md, ARCHITECTURE.md, docs/*.md, build.sh, packaging/ — cập nhật
   cho đúng thực tế mới. ARCHITECTURE.md mục Packaging viết lại cho
   AppImage mới. RELEASE_NOTES.md thêm mục v1.10.0 (daemon-first + Slint
   GUI + RAM số đo; ghi "pending tag").
3. KHÔNG đụng `crates/` (trừ nếu có comment/reference chết tới src-tauri —
   sửa tối thiểu, ghi trong report). `examples/minewrap.toml` giữ.
4. Icon copy (Bước 0 đã nhắc) + desktop file giữ tên Minewrap.

## Bước 3 — Test + build verify

- `cargo test --workspace` — baseline pass, KHÔNG test nào mất.
- `cargo build --workspace` + `cargo build -p minewrap-gui
  --no-default-features` — sạch warning (deny).
- `rg -i 'src-tauri|svelte|pnpm' --files-with-matches` ngoài docs lịch sử
  → phải rỗng (hoặc chỉ còn RELEASE_NOTES lịch sử — chấp nhận được, ghi rõ).

## Bước 4 — E2E AppImage trên máy thật (CÓ GUARD)

[MÁY — công thức đã kiểm chứng:]
- `wtype "text"` ổn; `wtype -k` hay chết ngầm — test đầu việc rồi mới tin.
- `click_abs X Y` / `click_multi X Y 2|3` / `wheel DELTAS [X Y]` (delta
  TRƯỚC) trong `~/dev-memtest/work/`. KHÔNG đọc ảnh vào context (422).
  `grim` save + `md5sum` từng ảnh. Pin PID bằng `pgrep -x`; kill đúng PID,
  KHÔNG `pkill -f`.

1. Chạy `packaging/build-linux.sh` → `dist/Minewrap-x86_64.AppImage` tồn
   tại (ls -la + sha256sum).
2. Scratch run: XDG_CONFIG_HOME + XDG_DATA_HOME trỏ `~/dev-memtest/work/
   p1c5-xdg`, HOME không đổi; `MINEWRAPD_BIN` KHÔNG set (thử đường
   locator cạnh-binary). Chmod +x AppImage, chạy, guard `pgrep -x
   minewrap-gui` + `pgrep -x minewrapd` (cả 2 phải sống; daemon spawn
   từ TRONG AppImage).
3. E2E tối thiểu (focus → act → grim → REST đối chiếu):
   - S1: GUI mở từ AppImage, sidebar hiện, daemon online.
   - S2: tạo instance qua wizard (p1c5stub, fakejava-echo) → start →
     console stream.
   - S3: stop + remove instance; quit GUI; daemon còn sống (design
     daemon-first) → kill daemon đúng PID.
   Ảnh: `~/dev-memtest/results/p1-c5/shot-s1..s3.png` + md5sum.
4. PSS từ AppImage run: 1×60 s idle, memsample.py, pgrep -x minewrap-gui
   (+ cây: GUI + minewrapd + fakejava nếu đang chạy) — đối chiếu budget
   < 60 MB GUI.

## Bước 5 — Commit + push + dọn + report

- Commit `[P1-C5]` (packaging switch + retire có thể 1 commit, message
  rõ 2 phần); push origin p1-c5. Dọn máy (kill đúng PID; KHÔNG pkill -f;
  git status sạch; scratch dirs GIỮ NGUYÊN cho GLM verify).
- `~/dev-memtest/results/p1-c5/REPORT.md`: trạng thái từng mục, AppImage
  sha256, bảng PSS, LOC xóa được (git diff --stat), deviations.
  Tin nhắn cuối ≥300 ký tự.

## Ràng buộc chung

- Repo sạch (Q8): KHÔNG commit tool/screenshot/kết quả/dist.
- KHÔNG sửa `crates/` (ngoài comment chết tối thiểu — tách commit nếu cần).
- App thật của user: không đụng.
- Nếu một mục không làm được — ghi rõ trong report, KHÔNG bịa.
