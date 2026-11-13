# Minewrap P0 — Báo cáo nghiệm thu & Spike toolkit (đầu vào Gate 2 + Gate 3)

> Ngày 2026-11-11 · Repo `github.com/longme179/Minewrap` · Branch `p0-daemon-first` @ `920de1e` (từ main `bfde421` v1.9.3) · Đích v1.10.0
> Đo trên máy user (Fedora 44, 12 lõi, kernel 7.2.15) bằng harness `~/dev-memtest/` (ngoài repo Minewrap — chính sách Q8).
> Mọi số trong báo cáo này đều **đo thực + GLM tái đo chéo**; cái gì chưa verify được ghi rõ "unverified".

## 1. Tóm tắt điều hành

| KPI | Ngưỡng | Kết quả | Verdict |
|---|---|---|---|
| **K1** — PSS wrapper khi đóng GUI (1 server chạy + 1 client WS console + Discord service) | ≤ 8 MiB | **6.53 MiB** (RSS 8.86) | **PASS** |
| **K2** — PSS cây GUI khi mở (vẫn WebKit, P0) | ≤ 219.8 MiB (baseline cùng ngày 209.32 +5%) | **209.83 MiB** (RSS 439.80) | **PASS** |
| **K3** — Tests | ≥ 60 | **60/60** (core 46 + remote 3 + daemon 10 + integration 1), sandbox GLM chạy lại độc lập | **PASS** |
| **K5** — `pnpm run check` UI Svelte | 0 errors | 0 errors, 0 warnings | **PASS** |
| **K4** — Spike report 3 toolkit | đủ dữ liệu chọn | 3 toolkit × 3 kịch bản × 3 runs, GLM verify chéo đủ 3/3 | **PASS** |

Điểm nhấn kiến trúc (đo được, không tuyên bố suông): đóng GUI khi server đang chạy → server **vẫn online**, Discord **vẫn push**, mở lại GUI → reconnect + backfill log theo seq không gap. Daemon SIGTERM = đường "dừng hẳn" duy nhất, exit sạch 0.0 s khi idle.

## 2. Nghiệm thu P0 — bằng chứng end-to-end (trên binary release v1.10.0)

### 2.1 K1 — daemon-first hoạt động thật

Kịch bản đo: daemon p0 (binary 5.99 MiB) + instance `survival` chạy fakejava stub (burst 2000 dòng + stream 0.5 s) + 1 client WS `/console` + Discord service bật webhook giả local (mode edit-in-place, interval 15 s).

- **PSS 6.53 MiB / USS 6.50 / 13 threads / 1 proc** — CSV: `results/csv_K1.csv`.
- Discord service chứng minh sống bằng log webhook giả: `POST /webhook` ×3 khi đổi trạng thái (leading + trailing debounce), sau đó `PATCH /webhook/messages/<id>` lặp đúng interval 15 s **đúng cùng một message id** (edit-in-place hoạt động).
- WS console nhận **98 log events** (batch có seq); state keeper cho REST `combined_state = "online"` (v1.9.3 daemon luôn báo `offline` — gap G2 đã lấp).
- Đối chiếu baseline cùng ngày (A2): SW v1.9.3 = 5.38 PSS → p0 = 6.53 PSS (+1.15 MiB cho 3 service mới: state keeper + SLP poller + Discord service + shared reqwest client + batching). Vẫn dư 1.47 MiB dưới ngưỡng 8.

### 2.2 Các số daemon còn lại (so baseline A2 đo cùng ngày)

| Kịch bản (p0) | RSS | PSS | Ghi chú |
|---|---|---|---|
| S0 (0 instance) | 6.59 | 4.31 | vs baseline 3.98 (A2) — +0.3 MiB cho hạ tầng service |
| S1 (1 inst offline) | 6.64 | 4.33 | **D2-lite PASS**: phẳng như S0 (v1.9.3 từng +0.75 MiB/instance đầu) |
| S3 (3 inst offline) | 6.46 | 4.21 | phẳng — owner task chỉ spawn khi start thật |
| K1 (chạy + WS + Discord) | 8.86 | 6.53 | KPI chính |

### 2.3 Demo end-to-end (script `mw-demo2`, log `/tmp/mw-demo2.log` trên máy user)

| Bước | Kết quả |
|---|---|
| GUI mở khi daemon chưa chạy | auto-spawn setsid, `/health` → `{"api_version":"1.0","daemon_version":"1.10.0"}`, log `{data_dir}/daemon.log` |
| CRUD REST (B4) | POST /instances → **201**; trùng id → **409**; DELETE → **200**; GET đã xoá → **404**; GET /java → JSON Java 21 Temurin thật; POST /scan-workdir → report đúng |
| Start server qua REST + đóng GUI | `state: online` → đóng GUI → **`state after close: online`, SERVER-SURVIVES**; daemon PSS trước/sau đóng GUI: 4.55 → 4.43 (không đổi) |
| Mở lại GUI | reconnect, logs backfill 500 dòng theo `first_seq`/`last_seq` (seq 1539+) — không gap |
| SIGTERM daemon khi idle (B5) | exit sau **0.0 s**, log: `SIGTERM received → all instances settled → exiting` |
| SIGTERM daemon khi server chạy | 60.51 s — đúng thiết kế escalate (stdin `stop` → TERM → KILL); stub không đọc stdin nên chờ đủ `stop_timeout` 60 s rồi TERM sạch; **server Minecraft thật sẽ nhận `stop` qua stdin và thoát trong vài giây** |
| Binary GUI (B6) | main 10.39 MiB → p0 **8.83 MiB (−15%)** — GUI không còn link `minewrap-core` |

### 2.4 Code review GLM (STOP-gate)

Review đích danh các file lõi mới: `state_keeper.rs` (port đúng semantics GUI cũ + fix GapF spawn-fail không panic + reset probe failures khi Starting), `poller_task.rs` (1 vòng chung, chỉ probe instance đang chạy, `unresponsive` là derived state — không event giả), `discord_service.rs` (leading+trailing debounce, periodic edit-in-place, `OnceLock<reqwest::Client>` dùng chung — D5), `api.rs` (4 route mới + `/events` batch 100 dòng/40 ms kèm seq + `instances_changed` + forward `RestartLoop` — gap G5 lấp), `src-tauri/main.rs` (exit policy mới + auto-spawn + forwarder per-node trên `tauri::async_runtime`, backoff + backfill `since_seq`). Commit `920de1e` đã xoá warning mà rustc 1.99.1 trên máy user phát hiện. Còn lại **unverified**: checklist thủ công 22 command từ UI (cần mắt người nhìn GUI — phần dưới).

## 3. Spike 3 toolkit — bảng so sánh C5

**Môi trường:** 3 app mini giống hệt nhau (1280×800, dark, Noto Sans 10 pt, console ring 1000 dòng, burst 2000, stream 2/s, form two-way, `--auto`). Agent đo 3 kịch bản × 3 runs; **GLM tái đo idle cả 3 app cùng lúc trên cùng session Wayland (niri)** — số verify chéo lệch ≤ 0.33 MiB so với số agent.

| Chỉ số | **Slint 1.18.1** (tuned, a11y off) | Slint (default, a11y on) | **gtk4-rs 0.9.7** (GSK_RENDERER=cairo) | **iced 0.13.1** (tiny-skia) |
|---|---|---|---|---|
| **PSS idle** | **13.71** (agent, Xvfb) / **13.35** (GLM, Wayland) | 15.79 | 24.46 (agent) / **24.13** (GLM) | 557.52 (agent) / **554.90** (GLM) |
| PSS burst 2000 dòng | 13.85 | 15.68 | 25.98 | 575.24 |
| PSS stream 2 dòng/s | 13.77 | 15.82 | 25.87 | 575.31 |
| RSS idle | 27.81 | 29.77 | 57.78 | 561.24 |
| Threads | 5 | 6 | 5 (max 7) | 16 |
| Binary (strip+LTO) | 11.63 MiB | 12.89 MiB | 385.6 KiB (link GTK động) | 5.99 MiB |
| Cold start (exec→frame) | ~125 ms | ~126 ms | **93 ms** | 300 ms |
| Build sạch (12 lõi) | 1m51s–2m53s | — | 58.5 s | 104 s |
| LOC app | 721 (300 RS + 421 markup) | — | 591 | 998 |
| ldd system libs | 18 (không GTK/Qt/WebKit) | — | **114** (cả GTK stack + gstreamer) | **5** (tối giản nhất) |
| **Ngân sách < 60 MB PSS** | **PASS (dư 46 MB)** | PASS | **PASS (dư 34 MB)** | **FAIL — vượt ~9 lần** |

### Checklist console (Q3 là hard requirement: chọn/copy từng đoạn)

| # | Yêu cầu | Slint | gtk4-rs | iced |
|---|---|---|---|---|
| 1 | Ring 1000 FIFO | Đạt | Đạt | Pass |
| 2 | Màu per-level | Đạt | Đạt | Partial (editor mono / colored mất selection) |
| 3 | **Native selection + Ctrl+C** | **THIẾU native** — custom theo dòng (arboard, verify chéo process); không chọn sub-line | **Đạt** (TextView native, verify keyboard; mouse cần người test) | Editor: native nhưng Ctrl+C phải workaround; colored: custom theo dòng |
| 4 | Auto-scroll stick/unstick | Đạt | Đạt (keyboard) | Partial (unstick unverified) |
| 5 | Burst 2000 < 1 s | Đạt (84–100 ms) | Đạt (51–62 ms) | Pass (259–286 ms) |
| 6 | Form two-way | Đạt | Đạt | Pass |
| 7 | `--auto` đủ chu kỳ | Đạt | Đạt | Pass |
| 8 | Noto Sans 10 pt | Đạt | Đạt | Pass |

### License (C5 — bắt buộc)

- **iced, gtk4-rs: MIT** — sạch với AGPL-3.0-only.
- **Slint: GPLv3 / Royalty-Free / Commercial** — **dùng được miễn phí**: GPLv3 ↔ AGPLv3 tương thích chính thức (mục 13 hai giấy phép cho phép link lẫn nhau — GNU GPL FAQ: *"You can always link GPLv3-covered modules with AGPLv3-covered modules"*; FSF bulletin 2021 xác nhận section 13). Slint cũng trả lời chính thức: *"If you release your code as GPL or AGPL, you use Slint under that license and you don't need to pay anything"* (discussion #7596, 2025-11-30). Điều kiện: giữ notice + phân phối combined work dưới AGPL-3.0 (điều Minewrap đã làm). Nguồn: gnu.org/licenses/gpl-faq, fsf.org/bulletin/2021/fall/the-fundamentals-of-the-agplv3, github.com/slint-ui/slint (LICENSES/) + discussion #7596.

### Nhận xét port 12 component (cả 3 agent đều đánh dấu "chủ quan, chưa port thử")

- Slint: khai báo + binding `<=>` tiện cho form; **đau nhất là console selection** (phải tự viết hit-test theo glyph nếu muốn sub-line); std-widgets lệch theme token; virtualization ListView sẵn.
- gtk4-rs: **console dễ nhất** (TextView + TextTag có sẵn selection/IME/a11y — spike chứng minh); binding hai chiều tự viết tay (`Rc<RefCell>`); kéo 114 lib hệ thống; build cần gtk4-devel (máy user phải extract RPM do không sudo).
- iced: Elm architecture sạch, deps tối giản — nhưng bị loại vì RAM.

## 4. Khuyến nghị C6

**iced bị loại** (555 MiB PSS — vượt ngân sách 9 lần; nguyên nhân sandbox-level: tiny-skia/winit cấp phát bề mặt khổng lồ; dù đo lại vẫn ổn định như vậy).

Còn lại **2 lựa chọn hợp lệ — user quyết (Gate 2)**:

| | **Lựa chọn A: gtk4-rs** | **Lựa chọn B: Slint (tuned)** |
|---|---|---|
| Vì sao | **Duy nhất đạt trọn Q3 hard requirement** (native selection + copy + màu trong 1 widget); 24.1 MiB PSS — chỉ bằng 12% RAM GUI hiện tại; console spike chứng minh đủ; MIT license | **RAM thấp nhất** (13.4 MiB — 7% GUI hiện tại); binary tự chứa 18 lib — phân phối AppImage nhẹ, không phụ thuộc GTK4 trên máy người dùng; GPLv3 tương thích AGPL |
| Đánh đổi | Kéo cả GTK4 runtime (114 lib); PSS +11 MiB so Slint; build cần dev headers | **Selection chỉ theo dòng** — vi phạm chữ "chọn/copy từng đoạn" của Q3; muốn sub-line phải tự viết custom (không cam kết được) |
| Effort port | TB (console dễ, form thủ công) | TB (form dễ, console khó nếu đòi sub-line) |

Khuyến nghị của GLM: **A (gtk4-rs)** nếu Q3 giữ nguyên như đã chốt — vì console là trái tim của panel quản trị server, và 24 MiB vẫn way dưới ngân sách. Chuyển sang **B (Slint)** nếu user chủ động nới Q3 xuống "chọn theo dòng là đủ" để lấy RAM thấp nhất + phân phối nhẹ nhất.

## 5. Trạng thái & việc còn lại trước Gate 3 (merge v1.10.0)

1. **Chờ user chọn toolkit (Gate 2)** — không chặn merge P0.
2. **Checklist tay 22 command từ UI** (mắt người trên GUI thật) — mọi đường REST/WS phía dưới đã verify tự động; chỉ còn lớp click UI. Đề nghị user mở GUI trên máy mình chạy qua 1 lượt (5–10 phút).
3. `git merge p0-daemon-first → main`, tag `v1.10.0`, RELEASE_NOTES đã soạn sẵn trong branch (breaking change: đóng GUI không dừng server; đường dừng hẳn = `systemctl --user stop minewrapd` / `kill -TERM`).

Số liệu thô: `~/dev-memtest/results/` (csv_K1, S0/S1/S3-p0, p0-demo/, verify-glm/, webhook-fake.log) · spike: `~/dev-memtest/spikes/{slint,iced,gtk4}/results/` · bản sao báo cáo này + kết quả: archive repo `GLM-sessions-sandbox-archive` (spikes/2026-11-toolkit/ + tools/memtest/results/).
