# Minewrap C1 spike — Slint (P0 / Phase C)

> **Q8:** toàn bộ mã + kết quả nằm tại `~/dev-memtest/spikes/slint/`; **không** commit/push gì
> vào repo Minewrap, không sửa repo khác. Ngày đo: 2026-11-11.

## 0. Tóm tắt

| | default (a11y ON) | tuned (a11y OFF) |
|---|---|---|
| PSS idle 60 s | **15.79 MiB** | **13.71 MiB** |
| PSS burst 30 s | 15.68 MiB | 13.85 MiB |
| PSS stream 60 s | 15.82 MiB | 13.77 MiB |
| RSS idle | 29.77 MiB | 27.81 MiB |
| threads | 6 | 5 |
| binary (strip+LTO) | 13,521,032 B (12.89 MiB) | 12,193,928 B (11.63 MiB) |
| cold start (spawn → READY) | 126.2 ms [124.3–1306.6]* | 125.2 ms [123.5–127.1] |
| build clean `--release` | **2m53s** (12 lõi) | 1m51s (incremental, không phải clean) |

\* 1 outlier 1306.6 ms trong 5 lần (page-cache/CPU hiccup); 4 lần còn lại 124.3–126.8 ms.
Xem §6.

## 1. Environment (protocol C4)

| Mục | Giá trị |
|---|---|
| Máy | Fedora 44 Workstation, 12 lõi, 14 GiB RAM |
| Kernel | `7.2.15-200.fc44.x86_64` |
| Session gốc | Wayland (niri), `WAYLAND_DISPLAY=wayland-1` |
| **Display đo** | **Xvfb :99, 1280×800×24** (`xorg-x11-server-Xvfb 21.1.25`) |
| Cách có Xvfb | Máy **không** có sẵn Xvfb; `sudo` cần mật khẩu → **không cài được**. Đã `dnf download` RPM và giải nén cục bộ vào `/tmp/opencode/xvfb-rpm/` (không thay đổi hệ thống). `xwininfo`/`xwd`/`xdotool` cũng chạy từ bản giải nén này. |
| Toolkit | Slint **1.18.1**, backend `winit-software` (`SLINT_BACKEND=winit-software`), renderer software (feature `renderer-software`, **không** bật `renderer-femtovg`) |
| Rust | `rustc 1.99.1 (58cf8f9c3 2026-10-13)` / `cargo 1.99.1` |
| Font | `Noto Sans` 10 pt toàn app (`default-font-family`/`default-font-size`); `fc-match "Noto Sans"` → `/usr/share/fonts/google-noto/NotoSans-Regular.ttf` |
| Locale | `LANG=en_US.UTF-8`, `LC_NUMERIC=en_US.UTF-8` |
| Clipboard dep | `arboard 3.7.0` (backend X11) |
| Cửa sổ | 1280×800 tại +0+0, mapped — `evidence/xwininfo-tree.txt` |

Không có WM chạy trên Xvfb; cửa sổ Slint map trực tiếp ở 0,0. `xdotool windowfocus`
được dùng để gán X input focus.

## 2. Bảng đo (memsample.py 1 Hz trên cây process app)

Mỗi ô = **median của 3 runs [min–max trên toàn bộ mẫu của 3 runs]**, đơn vị MiB.
Cây process: `procs = 1` (app không spawn subprocess; Slint thuần 1 process).
`memsample.py --pid <app> --seconds <N> --interval 1.0`.

### default (accessibility ON — feature mặc định `slint/accessibility`)

| Kịch bản | runs | RSS | PSS | USS | threads | swap |
|---|---|---|---|---|---|---|
| idle 60 s | 3×60 mẫu | 29.77 [27.11–29.90] | **15.79 [13.16–15.85]** | 13.32 [10.68–13.36] | 6 | 0 |
| burst 30 s (`--auto`, burst tại +10 s) | 3×30 mẫu | 29.81 [29.45–29.90] | **15.68 [15.48–15.80]** | 13.22 [13.00–13.35] | 6 | 0 |
| stream 60 s (`--auto-stream`) | 3×60 mẫu | 29.95 [29.55–30.01] | **15.82 [15.48–15.86]** | 13.34 [13.03–13.39] | 6 | 0 |

### tuned (accessibility OFF — `cargo build --release --no-default-features`)

| Kịch bản | runs | RSS | PSS | USS | threads | swap |
|---|---|---|---|---|---|---|
| idle 60 s | 3×60 mẫu | 27.81 [27.61–27.84] | **13.71 [13.62–13.89]** | 11.25 [11.12–11.39] | 5 | 0 |
| burst 30 s | 3×30 mẫu | 27.95 [27.52–28.09] | **13.85 [13.65–13.89]** | 11.37 [11.18–11.43] | 5 | 0 |
| stream 60 s | 3×60 mẫu | 27.79 [27.74–27.94] | **13.77 [13.57–13.86]** | 11.29 [11.10–11.38] | 5 | 0 |

**Đọc số:** bật accessibility tốn **~2.1 MiB PSS**, **+1 thread**, **+1.33 MB binary**
(accesskit/atspi). Console đầy 1000 dòng + update liên tục (burst/stream) **không**
làm tăng RSS/PSS đáng kể so với idle (chênh ≤0.14 MiB) — ring 1000 dòng giữ nguyên
bộ nhớ sau khi đầy.

### Jitter run-to-run (AC: ≤ 0.15 MiB)

| Config/scenario | spread median RSS giữa 3 runs | Đạt AC? |
|---|---|---|
| default/idle | 0.304 MiB | ✗ |
| default/burst | 0.293 MiB | ✗ |
| default/stream | 0.234 MiB | ✗ |
| tuned/idle | 0.219 MiB | ✗ |
| tuned/burst | 0.510 MiB | ✗ |
| tuned/stream | 0.153 MiB | ✗ (sát ngưỡng) |

**AC jitter KHÔNG đạt (0.15–0.51 MiB).** Quan sát trong CSV: một số run có RSS/PSS tụt
giữa chừng (ví dụ idle-1: 29.74 → 27.92 MiB lúc ~30 s, USS 13.29 → 11.46) rồi giữ
nguyên — đây là page reclaim của page private-clean/file-backed (font/mmap), không
phải app cấp phát thêm. Đề xuất cho lần đo chéo toolkit: warm-up 10 s rồi mới bắt đầu
cửa sổ đo, và đối chiếu cả khoảng [min–max] chứ không chỉ median.

## 3. Cold start (exec → frame đầu)

`READY` in ra stderr bởi **timer 50 ms sau `ui.show()`** — `set_rendering_notifier()`
trả `Unsupported` với backend winit-software (`READY_NOTIFIER_UNSUPPORTED` trong log),
nên **không có tín hiệu AfterRendering thật**. Vì vậy cold-start chứa hằng số +50 ms;
số thật sẽ nhỏ hơn ~50 ms. Đã xác nhận cửa sổ đã vẽ bằng screenshot tại thời điểm READY
(`results/cold_default.png`, `results/cold_tuned.png`).

| Config | 5 lần (ms) | median [min–max] |
|---|---|---|
| default | 126.2, 1306.6, 124.3, 124.7, 126.8 | **126.2 [124.3–1306.6]** |
| tuned | 127.1, 126.7, 125.1, 125.2, 123.5 | **125.2 [123.5–127.1]** |

(Đợt đo 3-run đầu tiên của `measure.py`: default `[130.0, 1478.8, 128.0]`,
tuned `[1402.6, 126.7, 127.2]` — cùng hiện tượng 1 outlier ~1.3–1.5 s.)

## 4. Binary / build / LOC / deps

- **Binary** (`lto=true, codegen-units=1, strip=true`):
  - default: `13,521,032 B` (12.89 MiB)
  - tuned (no a11y): `12,193,928 B` (11.63 MiB)
- **Build clean** `cargo clean && time cargo build --release` (12 lõi):
  **2m53s wall** (173.45 s), user 648.53 s, sys 55.95 s, max RSS 1.34 GB.
  Build tuned: 1m51s (incremental sau build default — không phải số clean).
- **LOC** (`wc -l`, không có cloc trên máy):
  - Rust: **300** (`src/main.rs` 285 + `src/bin/clipdump.rs` 12 + `build.rs` 3)
  - Slint markup: **421** (`ui/main.slint`)
  - **Tổng app: 721 LOC**; thêm `measure.py` 164 dòng (tooling đo, không tính app).
- **ldd top-level (18 dòng)** — không có GTK/Qt/WebKit:
  `libfontconfig, libfreetype, libxml2, libharfbuzz, libglib-2.0, libpng16, libz,
  libbz2, liblzma, libbrotli*, libgraphite2, libpcre2-8, libgcc_s, libm, libc`.
  X11 (`libX11`, `libxcb`, `libxkbcommon`) được nạp **động (dlopen)** bởi winit nên
  không xuất hiện trong `ldd`.

## 5. Checklist nghiệm thu console (kết quả THẬT)

| # | Yêu cầu | Đạt / Thiếu | Ghi chú + bằng chứng |
|---|---|---|---|
| 1 | Ring đúng 1000 dòng FIFO | **Đạt** | `RING=1000`, `VecDeque` + `VecModel` FIFO. Test: preload seq 1–1000, burst 2000 → đỉnh ring là **seq=2001**, status “1000 lines in ring” (`evidence/06-ring-fifo-top.png`, `evidence/ring-fifo.log`). |
| 2 | Màu per-level INFO/WARN/ERROR/DEBUG | **Đạt** | INFO `#f8fafc`, WARN `#f59e0b` (state-starting), ERROR `#ef4444` (destructive), DEBUG `#38bdf8` — **DEBUG không có token trong tokens.css**, là màu bổ sung, đã ghi rõ. Ảnh: `01-window-idle.png`. |
| 3 | Native selection + Ctrl+C copy | **THIẾU native — đạt bằng custom (line-granularity)** | `ListView` của Slint **không có** text selection. Đã tự làm overlay `TouchArea`: kéo chuột chọn theo dòng, Ctrl+C copy qua `arboard`. Kiểm chứng **cross-process**: app chạy, drag 4 dòng, Ctrl+C → `clipdump` (process khác, cùng X server) đọc được đúng 4 dòng/237 ký tự (`evidence/clipboard-roundtrip.txt`). Hạn chế: chọn **theo dòng**, không chọn được chuỗi con trong dòng; không có double-click word-select. |
| 4 | Auto-scroll stick + ngắt khi kéo lên + jump to latest | **Đạt** | Stick mặc định; wheel lên → `stick=false`, view đứng yên (không bị kéo về đáy sau 1.2 s); nút overlay “Jump to latest” hiện và bấm quay lại đáy (`03-…`, `04-…`). Có thêm PageUp/PageDown/End. **Lưu ý:** kéo-thả chuột để pan bị overlay selection chiếm; cuộn bằng wheel/scrollbar/phím. |
| 5 | Burst 2000 dòng < 1 s không khựng | **Đạt (theo số đo trong app)** | Nạp theo batch 400 dòng/20 ms: `BURST_DONE` **84.1–100.4 ms** cho 2000 dòng (4 lần đo: 84.1, 96.3, 100.0, 100.4 ms). Không đo frame-time/dropped-frame (không có instrumentation) — “không khựng” xác nhận bằng mắt + burst chạy trong lúc cửa sổ vẫn nhận input. |
| 6 | Form two-way (Apply đổi tên sidebar) | **Đạt** | `text <=> root.form-name` (two-way binding), ComboBox 4 option (`java21 · jar`, `java17 · jar`, `java21 · script`, `custom cmd`). Test: chọn srv-alpha, sửa “prod-east”, Apply → sidebar đổi tên (`07-form-rename.png`); chọn profile 2 → log `APPLY idx=0 name=srv-alpha profile=1`. Popup ComboBox mở được (`08-`, `09-`). |
| 7 | `--auto` 10s→burst→60s stream→exit | **Đạt** | `START`→`READY` +129 ms; `BURST_START` tại **+10.079 s**; `STREAM ON`; `BURST_DONE 100.0 ms`; `AUTO_EXIT` tại **+70.079 s**; exit code **0** (`evidence/auto-full.log`). |
| 8 | Font Noto Sans 10 pt | **Đạt** | `default-font-family: "Noto Sans"`, `default-font-size: 10pt`; `fc-match` trả NotoSans-Regular.ttf; ảnh render đúng. (Console dùng Noto Sans — không monospace — theo yêu cầu loại biến số font.) |

## 6. Ergonomics + độ khó port (nhận xét chủ quan, đánh dấu rõ)

**Điểm mạnh**
- Khai báo UI bằng `.slint` rất gọn: toàn bộ layout + style + binding 421 dòng; state
  hai chiều `<=>` gần như miễn phí; vòng lặp model + virtualization (ListView) sẵn có.
- Memory thấp: PSS ~13.7–15.8 MiB cho app 1280×800 có 1000 dòng console + stream; binary
  12–13 MB; không kéo GTK/WebKit.
- Tốc độ proto rất nhanh (app đầy đủ trong ~1 buổi), hot-reload/live-preview có sẵn
  (không test trong spike này).

**Điểm đau (quan trọng cho P1/P2)**
1. **Console selection**: không có native selection trong `ListView`. Custom overlay
   chỉ đạt mức “chọn theo dòng”. Nếu Minewrap cần copy chính xác như terminal/WebKit
   (chọn ký tự, double-click chọn từ, copy vùng), phải tự viết hit-test theo glyph
   hoặc dùng `TextEdit` read-only (mất màu per-level). Đây là **rủi ro lớn nhất** khi port.
2. **Styling std-widgets**: `LineEdit`/`ComboBox` dùng palette Fluent nội bộ; global
   `Palette` chỉ `out` nên **không override được token** → form lệch tông so với app
   (token dark vs Fluent xám). Muốn “không dùng màu hệ” tuyệt đối phải tự viết widget.
3. **Batching model**: `VecModel` không có API “drop N dòng đầu” hàng loạt; mỗi dòng
   FIFO = 1 `remove(0)` + 1 `push`. Với 1000 dòng vẫn ổn (burst 2000 ~100 ms) nhưng
   nếu ring lớn hơn (10k+) cần thiết kế lại (deque model riêng).
4. **Accessibility**: bật a11y tốn ~2.1 MiB PSS + 1 thread + 1.3 MB binary. Cần quyết
   định sản phẩm; Slint a11y chưa được kiểm chứng với screen reader thật ở đây.
5. **Rendering notifier**: winit-software không hỗ trợ → không đo được frame-accurate,
   cũng không hook được “first paint”. Nếu cần số cold-start chuẩn, phải đo bằng
   screenshot/trace ngoài hoặc dùng backend khác.
6. **License**: Slint = GPLv3 / Royalty-Free / Commercial. Minewrap AGPL-3.0-only →
   cần C5 xác minh tương thích + đọc Royalty-Free terms trước khi chọn (ngoài phạm vi
   spike này; **chưa kết luận**).

**Ước lượng port 12 component hiện có** (theo `build/Minewrap/ui/src/components/`):

| Component | Độ khó | Ghi chú |
|---|---|---|
| Console | **Cao** | selection/copy + 1000 dòng + burst (đã làm, xem trên) |
| Dashboard | Thấp | card/stat tĩnh, binding dễ |
| Nodes | Thấp–TB | list + badge trạng thái (đã có mẫu sidebar) |
| AddInstance / Wizard | TB | nhiều form + validate; binding `<=>` tốt, nhưng cần state machine |
| JavaPicker | TB | list chọn + filter |
| Mods | TB–Cao | bảng/list + toggle + file I/O; table view của Slint còn non |
| Notifications | TB | toast overlay, timer |
| Properties | TB | form key/value động |
| Select | Thấp | dropdown (std ComboBox dùng được nhưng lệch theme) |
| Settings | TB | nhiều nhóm form, persistence |
| App shell / tabs | TB | cần tab + routing tự viết |
| Dialog/confirm | Thấp–TB | popup/dialog API cần tự dựng |

## 7. Cách tái lập (cho GLM re-measure)

```bash
# Xvfb (bản giải nén, không cần root)
/tmp/opencode/xvfb-rpm/usr/bin/Xvfb :99 -screen 0 1280x800x24 -nolisten tcp &
cd ~/dev-memtest/spikes/slint
DISPLAY=:99 SLINT_BACKEND=winit-software ./mw-spike-slint-default          # idle
DISPLAY=:99 SLINT_BACKEND=winit-software ./mw-spike-slint-default --auto   # burst@10s, exit@70s
DISPLAY=:99 SLINT_BACKEND=winit-software ./mw-spike-slint-default --auto-stream  # stream 2/s, exit@70s
python3 measure.py default      # chạy lại toàn bộ 3 kịch bản × 3 runs + cold start
```

Binaries đã build sẵn: `mw-spike-slint-default`, `mw-spike-slint-tuned`,
`target/release/clipdump`. Kết quả thô: `results/csv_*.csv`, `results/json_*.json`,
`results/summary.json`, log app: `results/logs/run_*.log`.

## 8. Những gì CHƯA verify / đã bỏ qua

1. **Selection native** đúng nghĩa (sub-line) — không có; chỉ custom theo dòng.
2. **Cold start frame-accurate** — READY là timer 50 ms sau `show()`, không phải
   AfterRendering (backend không hỗ trợ notifier). Số cold start vì thế **cộng thừa ~50 ms**.
3. **Frame-time / dropped frames** khi burst — không instrument; chỉ có thời gian drain
   model (84–100 ms) + quan sát bằng mắt.
4. **Wayland-direct** — không chạy; toàn bộ đo trên Xvfb (không cài được Xvfb hệ thống
   vì `sudo` cần mật khẩu, dùng RPM giải nén cục bộ).
5. **Accessibility thực tế** (screen reader/AT-SPI đọc đúng role/label) — chỉ đo khác
   biệt bật/tắt (thread, RAM, binary), chưa test AT.
6. **Selection khi ring trượt** — selection lưu theo index; nếu dòng mới chèn vào đầu
   trong lúc đang chọn, vùng chọn sẽ lệch. Chưa xử lý.
7. **Pan bằng kéo chuột** trên console — bị overlay selection chiếm; chỉ wheel/scrollbar/phím.
8. **Clipboard trên Wayland-direct** — chỉ test X11 (`arboard` X11 + `clipdump`).
9. **Jitter AC ≤0.15 MiB** — không đạt (0.15–0.51 MiB), xem §2.
10. **Build time tuned clean** — chỉ có số incremental (1m51s).
11. **LOC** bằng `wc -l` (không có `cloc` trên máy).
12. **License Slint ↔ AGPL** — chưa kết luận (C5 của GLM).
13. **MANIFEST** — `sha256sum -c` báo **1 file FAILED: `results/env-check.md`** (file kết
    quả cũ, sửa trước phiên này); 16/16 file còn lại OK. Không sửa file đó.
