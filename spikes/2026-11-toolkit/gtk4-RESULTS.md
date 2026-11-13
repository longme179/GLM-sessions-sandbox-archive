=====SPLIT-MARKER=====
# C3 — gtk4-rs spike results (Minewrap P0, Phase C)

> Ngày đo: 2026-11-11 · Máy user · Q8: toàn bộ source/kết quả nằm tại
> `~/dev-memtest/spikes/gtk4/`, KHÔNG commit/push vào repo Minewrap.
> App: `mw-spike-gtk4` (GTK4-rs 0.9.7, edition 2024, release LTO/strip).

## 1. Môi trường đo

| Mục | Giá trị |
|---|---|
| Distro / kernel | Fedora Linux 44 (Workstation) / 7.2.15-200.fc44.x86_64 |
| CPU / RAM | AMD Ryzen 5 7535HS, 12 lõi / 14 GiB |
| Display | **wayland-direct**, niri 26.04, 1920×1080 @ scale 1.0 |
| Xvfb | **KHÔNG có**; `sudo dnf install` không chạy được (sudo cần mật khẩu) → đo Wayland-direct theo C4 |
| Toolkit runtime | GTK 4.22.5 (libgtk-4.so.1), cairo 1.18.6 |
| Rust | rustc/cargo 1.99.1 (Fedora 1.99.1-2.fc44) |
| gtk4-rs | gtk4 0.9.7 / gdk4 0.9.6 / glib 0.20.12 (Cargo.lock) |
| Renderer | **`GSK_RENDERER=cairo`** (bắt buộc, xem §7) |
| Font | Noto Sans, Pango resolve `Noto Sans 13.333px` = 10 pt @ 96 dpi |
| Locale | `en_US.UTF-8` |
| Window | 1280×800, float, đặt tại (0,0) bằng `niri msg` trước khi sample |
| Sampler | `~/dev-memtest/memsample.py` (smaps_rollup RSS/PSS/USS, 1 Hz, cây process) |

**Sai lệch môi trường (bắt buộc ghi rõ):** không có Xvfb nên mọi số dưới đây là
**wayland-direct (niri)**, không so chéo với Xvfb. Ngoài ra MANIFEST của harness
có 1 mismatch **từ trước phiên này**: `results/env-check.md` (mtime 13:58 sau
MANIFEST 13:51); các file còn lại OK. Không sửa harness/lịch sử đó.

## 2. Kết quả đo — 1 config (default/cairo) × 3 kịch bản × 3 runs

Đơn vị MiB. Ô = **median của 3 run-median [min–max giữa 3 run]**; threads =
median (max quan sát trong mẫu). Swap = 0 toàn bộ, procs = 1 (app không spawn con).

| Kịch bản | RSS | PSS | USS | Threads |
|---|---|---|---|---|
| idle 60 s | 57.78 [57.54–57.93] | 24.46 [24.21–24.54] | 15.42 [15.39–15.58] | 5 (max 7) |
| burst 30 s quanh 2000 dòng | 59.32 [59.14–59.61] | 25.98 [25.83–26.22] | 16.95 [16.80–17.40] | 5 (max 7) |
| stream 2 dòng/s 60 s | 59.01 [58.94–60.01] | 25.87 [25.63–26.73] | 16.79 [16.71–17.54] | 5 (max 8) |

Thống kê gộp toàn bộ sample (180 sample idle/stream, 90 sample burst):

| Kịch bản | RSS median [min–max] | PSS median [min–max] | USS median [min–max] |
|---|---|---|---|
| idle | 57.78 [57.47–57.93] | 24.45 [24.14–24.79] | 15.43 [15.36–15.61] |
| burst | 59.14 [57.74–59.61] | 25.98 [24.35–26.56] | 16.80 [15.51–17.44] |
| stream | 59.01 [58.81–60.01] | 25.87 [25.50–26.73] | 16.79 [16.70–17.54] |

Run-median từng run (để GLM đối chiếu khi tái đo):

| Run | idle RSS/PSS/USS | burst RSS/PSS/USS | stream RSS/PSS/USS |
|---|---|---|---|
| #1 | 57.78 / 24.21 / 15.39 | 59.61 / 26.22 / 17.40 | 58.94 / 25.87 / 16.71 |
| #2 | 57.54 / 24.54 / 15.42 | 59.32 / 25.83 / 16.95 | 60.01 / 26.73 / 17.54 |
| #3 | 57.93 / 24.46 / 15.58 | 59.14 / 25.98 / 16.80 | 59.01 / 25.63 / 16.79 |

**AC jitter run-to-run ≤ 0,15 MiB: KHÔNG ĐẠT.** Chênh median giữa 3 run:
PSS idle 0,32 / burst 0,39 / stream 1,09 MiB; RSS 0,39 / 0,47 / 1,07 MiB.
Trong-run (steady) RSS chỉ dao động 0,04–0,13 MiB; burst có +~1,5 MiB do cấp
phát texture/font cache. Nguyên nhân nghi ngờ: PSS chia theo shared lib với các
app desktop đang chạy song song (Firefox/OpenCode + spike iced/slint của phiên
khác), không phải app tự tăng. GLM nên tái đo khi desktop yên hơn.

Raw: `results/{idle,burst,stream}-run{1,2,3}.{csv,json,log}`.

## 3. Burst / ring / `--auto`

| Chỉ số | Kết quả |
|---|---|
| Burst 2000 dòng (đo trong 3 run) | **51 / 54 / 51 ms** (`BURST_DONE total_ms`) |
| Burst lần smoke cuối (binary final) | 62 ms |
| Thời gian xóa ring mỗi batch (max) | **57–95 µs** trong 3 run; max từng thấy 152 µs |
| Ring | đúng 1000 dòng FIFO; UI hiển thị `lines: 1000` |
| Bằng chứng ring | clipboard Ctrl+A/C 1000 dòng `#1005..#2004`; ảnh `final-burst.png`, `selection-final.png` |
| `--auto` | READY → burst **+10,033 s**; burst → AUTO_DONE **+60,500 s**; process tự exit (log `evidence/auto-final.log`) |

Batch 100 dòng/lần qua `timeout_add_local(1 ms)`; xóa tối đa 100 dòng/lần bằng
một `TextBuffer::delete(range)` — không re-render toàn list.

## 4. Cold start (exec → frame đầu)

Marker `READY <epoch_ms>` in ra từ `GdkFrameClock::after-paint` (frame đầu thực
sự được paint). 3 lần dedicated: **93 / 93 / 93 ms → median 93 ms [93–93]**.
12 lần launch tổng cộng (3 cold + 9 measurement) nằm trong **90–96 ms**.
Screenshot `evidence/cold-run{1,2,3}.png` chụp +1,5 s sau READY (để tránh frame
đang resize); bản thân số cold-start lấy từ marker, không từ screenshot.

Lưu ý: niri tile cửa sổ mới (936×1010) ngay khi map; script resize float
1280×800 sau đó ~0,3 s. Vì vậy **frame đầu tiên trong cold-start không phải
1280×800**; measurement bắt đầu sau resize + 1,2 s.

## 5. Binary / build / LOC

| Mục | Giá trị |
|---|---|
| Binary | `target/release/mw-spike-gtk4`, **394.832 B (385,6 KiB)**, stripped, PIE |
| sha256 | `b80eaaea8669540bf903fc61d0ece9a55940a1814ae0dcd795d9f8d734e3721d` |
| Build (clean target, 12 lõi) | **58,49 s real** (user 91,50 s, sys 11,34 s) |
| LOC app | **591** dòng `src/main.rs` + **12** dòng `Cargo.toml` |
| LOC phụ trợ | 79 dòng `run_measure.sh` (không tính app) |
| ldd | **114** entry; top-level gồm libgtk-4, libgio, libgobject, libglib, libgmodule, libpangocairo, libpango, libcairo, libharfbuzz(+subset), libfribidi, libcairo-gobject, libfontconfig, libgdk_pixbuf, libepoxy… (GTK kéo cả gstreamer) |

ldd top-20 (nguyên văn):

```
linux-vdso.so.1
libgtk-4.so.1 => /lib64/libgtk-4.so.1
libgio-2.0.so.0 => /lib64/libgio-2.0.so.0
libgobject-2.0.so.0 => /lib64/libgobject-2.0.so.0
libglib-2.0.so.0 => /lib64/libglib-2.0.so.0
libgcc_s.so.1 => /lib64/libgcc_s.so.1
libc.so.6 => /lib64/libc.so.6
libgmodule-2.0.so.0 => /lib64/libgmodule-2.0.so.0
libpangocairo-1.0.so.0 => /lib64/libpangocairo-1.0.so.0
libpango-1.0.so.0 => /lib64/libpango-1.0.so.0
libcairo.so.2 => /lib64/libcairo.so.2
libharfbuzz.so.0 => /lib64/libharfbuzz.so.0
libharfbuzz-subset.so.0 => /lib64/libharfbuzz-subset.so.0
libfribidi.so.0 => /lib64/libfribidi.so.0
libcairo-gobject.so.2 => /lib64/libcairo-gobject.so.2
libfontconfig.so.1 => /lib64/libfontconfig.so.1
libgdk_pixbuf-2.0.so.0 => /lib64/libgdk_pixbuf-2.0.so.0
libepoxy.so.0 => /lib64/libepoxy.so.0
libm.so.6 => /lib64/libm.so.6
libgstplay-1.0.so.0 => /lib64/libgstplay-1.0.so.0
```

Build shim: máy không có `gtk4-devel`/`gtk4.pc` và không sudo được. Đã tải RPM
`gtk4-devel-4.22.5`, `graphene-devel` rồi trích `.pc` + symlink `.so` vào
`.spike-pkgconfig/`; `.cargo/config.toml` set `PKG_CONFIG_PATH` trỏ vào đó.
Đây là workaround build trên máy này, **không phải** build hệ thống sạch.

## 6. Checklist nghiệm thu console (8 mục)

| # | Yêu cầu | Đạt / Thiếu | Ghi chú + bằng chứng |
|---|---|---|---|
| 1 | Ring đúng 1000 dòng FIFO | **Đạt** | `lines: 1000` (`final-burst.png`); clipboard đúng 1000 dòng `#1005..#2004` (`clipboard-final.txt`); trim bằng 1 range delete |
| 2 | Màu per-level INFO/WARN/ERROR/DEBUG | **Đạt** | trắng/vàng/đỏ/xanh (`final-burst.png`, `auto-stream.png`), `TextTag` foreground |
| 3 | Native selection + Ctrl+C copy | **Đạt** (keyboard; mouse chưa test) | `selection-final.png` (highlight toàn bộ) + clipboard 48.049 B/1000 dòng; không có pointer injection nên không test kéo chuột |
| 4 | Auto-scroll stick + ngắt khi kéo lên + jump | **Đạt** (scroll bằng keyboard) | `ring-top-1000.png`: Ctrl+Home → hiện “Jump to latest”; `jump-latest.png`: Enter → về bottom, nút ẩn; mouse-wheel chưa test |
| 5 | Burst 2000 dòng < 1 s, không khựng | **Đạt** | 51–62 ms; batch 100 dòng + xóa ≤100 dòng/lần; max trim 57–152 µs |
| 6 | Form two-way (Apply đổi tên sidebar) | **Đạt** | `form-edit.png` (gõ “renamed-5”) → `form-applied.png` (sidebar đổi); chọn row cập nhật form (`focus-tab2.png`) |
| 7 | `--auto` 10 s → burst → 60 s stream → exit | **Đạt** | `evidence/auto-final.log`: burst +10,033 s, AUTO_DONE +60,500 s, process exit; `auto-stream.png` lúc đang stream |
| 8 | Font Noto Sans 10 pt | **Đạt** | Pango context in `Noto Sans 13.333px` (10 pt @96dpi); ảnh screenshot đúng font |

## 7. Ghi chú kỹ thuật / ergonomics

- **Renderer:** GTK4 mặc định trên máy là NGL/Vulkan (thấy warning
  `vkAcquireNextImageKHR … VK_SUBOPTIMAL_KHR`). SPEC ghi “cairo (mặc định)”
  **không đúng** với GTK 4.22; spike ép `GSK_RENDERER=cairo` cho đúng mục tiêu
  không GPU. Mọi số đo là cairo, không phải renderer default.
- **TextView + TextTag** rất hợp console: selection/copy/IME/accessibility có
  sẵn, 1000 dòng không cần virtualization; trim ring cực rẻ.
- **Focus chain:** phải `set_can_focus(true)` cho TextView; Tab đi vào
  `GtkTextView` rồi `GtkText` (inner). Ctrl+A/C chỉ ăn khi focus ở `GtkTextView`.
- **State two-way** phải tự viết (Rc<RefCell> + callback); không có binding
  declarative như Svelte/Slint.
- **Dependency nặng:** 114 lib, kéo cả gstreamer; PSS ~24–26 MiB (shared lib
  được chia) — vẫn dưới KPI <60 MiB PSS.
- **Build:** cần dev headers/pkg-config; thiếu sudo là rào cản thực tế.

### Mức khó port 12 component (nhận xét chủ quan, CHƯA port thử)

| # | Component Minewrap | Độ khó (1–5) | Ghi chú |
|---|---|---|---|
| 1 | App shell / sidebar (`App.svelte`) | 2 | Box/ListBox + CSS token dễ |
| 2 | Dashboard | 3 | chart/progress phải custom drawing |
| 3 | Nodes | 2 | ListBox/ListView + badge; nhiều node cần ListView |
| 4 | Console | 2 | đã chứng minh bằng spike này |
| 5 | Properties | 3 | form binding thủ công |
| 6 | Settings | 3 | form + persist thủ công |
| 7 | AddInstance | 4 | validation/async/file dialog |
| 8 | Wizard | 4 | nhiều bước; GTK Assistant có nhưng logic tự viết |
| 9 | JavaPicker | 3 | FileChooser + scan version |
| 10 | Select | 1 | `DropDown` |
| 11 | Mods | 4 | list lớn/search/sort/file ops |
| 12 | Notifications | 2 | Revealer/Toast overlay |

## 8. Chưa verify / skipped (trung thực)

- **Xvfb path chưa chạy** (không có Xvfb, sudo cần password) → wayland-direct.
- **Mouse selection / wheel scroll chưa test** (không có `ydotool`/quyền
  `/dev/uinput`; chỉ có `wtype` keyboard). Đã test keyboard tương đương.
- **Jitter AC ≤0,15 MiB không đạt**; số thật ở §2, nghi do PSS shared-lib noise.
- **Frame đầu cold-start không ở 1280×800** (niri tile trước, resize sau).
- **Build không sạch hệ thống**: dùng `.spike-pkgconfig` trích từ RPM vì thiếu
  `gtk4-devel`; ABI link với runtime GTK 4.22.5.
- **Chưa đo renderer default (NGL/Vulkan)** để so sánh; chỉ đo cairo.
- **Chưa test** drag chọn bằng chuột, clipboard rich text/HTML, IME, accessibility
  screen reader, >2000 dòng burst, nhiều cửa sổ.
- Số đo chịu ảnh hưởng desktop đang chạy song song (Firefox/OpenCode + các spike
  iced/slint khác trên cùng máy).
- Port 12 component: **nhận xét chủ quan**, chưa viết code port.

## 9. Q8 / phạm vi

Toàn bộ code, log, CSV/JSON, screenshot nằm trong
`~/dev-memtest/spikes/gtk4/`. Không commit/push, không sửa `Minewrap` hay
`memsample.py`/harness. Chờ GLM review diff + tái đo ngẫu nhiên ≥1 kịch bản.
