# Minewrap: phương án giảm RAM (từ WebKit sang Rust thuần)

Nov 11, 2026 · @Long

## RAM đang nằm ở đâu

Phần lớn RAM nằm ở WebKit chứ không phải ở code Minewrap: cả cây process GUI chiếm khoảng 436 MiB RSS (196 MiB PSS), còn daemon chỉ vài MiB. Số đo lấy từ báo cáo kiến trúc v1.9.3 (máy 12 lõi, GUI idle, 1 instance offline, chưa mở console).

| Thành phần | RSS (MiB) | PSS (MiB) |
| --- | --- | --- |
| `minewrapd` (kể cả 1 server chạy + 1 client WS) | 5,6 – 7,4 | 3,2 – 5,1 |
| GUI Tauri, cả cây 3 process | 436 | 196 |
| – 2 process WebKit | 259 | \~122 |
| – shell Rust (GTK3 + WebKitGTK nạp trong process) | 178 | 74 |

- Các mục D1–D6 của báo cáo gộp lại tiết kiệm dưới 1 MiB; G1–G5 chỉ cắt được vài MiB trên 196 MiB PSS. Chỉ bỏ WebKit mới đổi được bậc độ lớn.
- Mục tiêu "process Tauri dưới 30 MB" không đạt được với WebKitGTK: riêng shell Rust đã 178 MiB RSS (74 MiB PSS).
- Số đo GUI là lúc idle, nên khi mở console sẽ cao hơn. Benchmark công khai cũng ghi nhận webview WebKit tốn RAM hơn kỳ vọng khi chạy app web thật (Tauri issue #5889).

## Các phương án

Có ba hướng, xếp theo hiệu quả trên công sức: P0 nên làm bất kể chọn gì, P1 là hướng "100% Rust", P2 là lối tắt nếu chấp nhận dùng trình duyệt.

### P0. Daemon-first, GUI là process riêng chỉ mở khi cần

- `minewrapd` (\~6 MiB) là lõi luôn chạy; GUI chỉ là client của daemon qua REST/WS mà daemon đã có. Đóng GUI thì toàn bộ phần WebKit biến mất, và khi không mở cửa sổ RAM của wrapper còn khoảng 6–7 MiB.
- GUI không cần nhúng core, tokio nhiều luồng và reqwest nữa; node "local" trở thành một node remote ở 127.0.0.1, khớp quy tắc "UI không tự spawn process".
- Đổi lại phải bỏ chính sách "đóng GUI = dừng mọi server". Bù lại, webhook Discord chạy được cả khi GUI đóng.
- Báo cáo ghi daemon hiện không có vòng poll trạng thái nền, và cũng không nhắc tới vòng push định kỳ 10 phút. Nếu chuyển sang daemon-first, hai thứ này phải nằm trong daemon (chi phí bộ nhớ chỉ vài chục KiB).

### P1. Thay UI WebKit bằng GUI Rust thuần

Không có benchmark so sánh công bằng giữa các toolkit; bảng dưới chỉ gom các ca đơn lẻ đã đọc được.

| Toolkit | Cách vẽ | Bằng chứng công khai | Rủi ro cho Minewrap |
| --- | --- | --- | --- |
| Slint | winit (X11 + Wayland), chọn bằng `SLINT_BACKEND=winit-software` | App giám sát rproc: \~135 MB (egui) xuống \~30 MB (Slint, tắt GPU), \~50 MB khi bật giám sát GPU; đo RSS, và bài viết cũng nhờ nhiều tối ưu khác. Một người khác đo hello world Slint 45–54 MB với cấu hình mặc định (Qt) | Console có màu, chọn/copy được cần thử riêng; đường vẽ động (Path) phải khai báo tĩnh khi dùng software renderer; kiểm tra giấy phép với AGPL-3.0 |
| iced | tiny-skia (CPU) thay wgpu | Chưa có số đo; một bình luận khuyên thử tiny-skia vì footprint iced chủ yếu là bộ nhớ cấp trước | Text không chọn được trừ TextEditor/TextInput; crate bên thứ ba `iced_selection` bổ sung chọn text |
| egui | wgpu hoặc glow | Bản egui của rproc \~135 MB; app wgpu thường khởi đầu 100+ MB | Không khuyến nghị; glow nhẹ hơn nhưng chưa có số đo |
| gtk4-rs | GTK4 | Không có số đo trong các nguồn đã đọc; bài rproc nhận xét kéo theo cả GTK runtime, baseline lớn | Chỉ Linux; cần thử renderer cairo thay GPU; `TextView` phù hợp cho log |

Thông tin thêm về Slint (docs 1.18.1): winit hỗ trợ cả X11 lẫn Wayland, `renderer-femtovg` là renderer mặc định, `accessibility` bật mặc định, và `system-tray` (SystemTrayIcon, dùng `ksni` trên Linux) cũng bật mặc định.

Maintainer của Slint cho biết trên desktop phần lớn bộ nhớ nằm ở cache font/ảnh và framebuffer (hai buffer 32-bit cho cửa sổ 1080p đã 16,5 MB), cộng thư viện hệ thống và driver đồ hoạ. Rủi ro lớn nhất của P1 là **console**: 1000 dòng có màu theo mức log, chọn và copy được, chịu được burst vài nghìn dòng mỗi giây.

### P2. Phục vụ UI Svelte từ `minewrapd`, mở bằng trình duyệt

- RAM của wrapper chỉ còn bằng daemon, và các node remote cũng có UI mà không cần cài thêm.
- Phần RAM trình duyệt không biến mất mà chuyển sang trình duyệt của bạn; mất cảm giác app desktop (tray, cửa sổ riêng).
- Cần bảo mật khi mở UI trên localhost: kiểm tra Host/Origin để chống DNS rebinding, và token không nằm trong URL.
- TUI (ratatui) là hướng bổ sung hợp lý để quản lý qua SSH, nhưng chưa có số đo nào để cam kết.

## Đề xuất cụ thể

Làm P0 trước, rồi dùng một đợt spike đo thật để chọn toolkit cho P1.

1. **P0 ngay:** chuyển sang daemon-first, thêm vòng poll trạng thái và vòng push Discord định kỳ vào daemon, GUI chỉ là client.
2. **Spike toolkit:** dựng cùng một mini-app cho Slint (`winit-software`), iced (tiny-skia) và gtk4-rs (cairo): sidebar, thanh trạng thái, form có select, console 1000 dòng có màu và chọn được, cho chạy burst. Đo bằng `memsample.py` và `scenario.py` của bạn, lấy PSS của cả cây process làm chỉ số chính.
3. **Ngân sách theo PSS:** chốt con số sau khi có số spike. Các ca đơn lẻ ở trên gợi ý khoảng 30–60 MB cho GUI Rust render bằng CPU, nhưng đó chưa phải số của app này.
4. **Port UI:** chuyển 12 component Svelte sang toolkit thắng, từng màn một. Skill ui-ux-pro-max không có stack Slint hay iced; chỉ dùng các domain `style`, `typography`, `ux`, `icons` làm tham chiếu, rồi tự đưa token màu và font vào toolkit.

### Xử lý danh sách tối ưu cũ

- **Giữ:** D1 (đặt `TOKIO_WORKER_THREADS` trong unit systemd, không tốn công), D2 nếu quản lý nhiều instance, D5 vì rẻ.
- **Bỏ:** G1–G5 vô nghĩa sau P1; D3, D4, D6 chỉ tiết kiệm cỡ KiB.

## Nguồn

Đã mở toàn trang:

- Báo cáo kiến trúc và đo bộ nhớ Minewrap v1.9.3 (tài liệu bạn cung cấp)
- [How I took my Rust GUI from 135 MB to 30 MB by ditching the GPU](https://dev.to/trystan_sarrade/how-i-took-my-rust-gui-from-135-mb-to-30-mb-by-ditching-the-gpu-2i7d)
- [r/rust: small footprint gui library (câu trả lời của maintainer Slint)](https://nyc1.lr.ggtyler.dev/r/rust/comments/1jzawxo/small_footprint_gui_library)
- [Slint: cargo features và backend](https://docs.slint.dev/latest/docs/rust/slint/docs/cargo_features/)

Chỉ đọc qua đoạn trích tìm kiếm, chưa mở toàn trang (nên coi là tham khảo):

- [Tauri issue #5889: benchmark bộ nhớ webview](https://github.com/tauri-apps/tauri/issues/5889)
- [iced\_selection](https://docs.rs/crate/iced_selection/latest)
- [r/rust: Rust GUIs và bộ nhớ của graphics API](https://redlib.hbubli.cc/r/rust/comments/17np5sl/rust_guis_why_are_modern_graphics_apis_so_heavy)
- [r/rust: thread rproc egui sang Slint (bình luận về iced + tiny-skia)](https://reddit.sentinel-team.org/posts/1tvqq9e/snapshots/2026-06-04T04%3A47%3A22.4424Z)
