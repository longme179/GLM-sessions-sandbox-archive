# KẾ HOẠCH MINEWRAP RAM COMPACT — ĐỢT 1: P0 (DAEMON-FIRST) + SPIKE TOOLKIT

**Trạng thái:** v1.1 — Phase A đã duyệt (kèm sửa đổi Q8: chính sách repo sạch); Phase B/C khởi động sau khi A xong
**Ngày:** 2026-11-11 (v1.1 cùng ngày — user duyệt Phase A)
**Repo:** `github.com/longme179/Minewrap` @ `main` `bfde421` (v1.9.3)
**Người thực hiện:** GLM (Z.ai) viết code daemon/core + review toàn bộ; OpenCode agent (`deepseek-v4.1-flash`, fallback `deepseek-v4-pro` / `-free`) chạy spike + đo số trên máy user; user giữ review-gate
**Phạm vi (đã chốt):** P0 daemon-first + spike 3 toolkit GUI Rust. Port UI thật sự (P1) thuộc đợt sau.

---

## 0. QUYẾT ĐỊNH ĐÃ CHỐT (phiên hỏi đáp 2026-11-11)

| # | Quyết định | Lựa chọn |
|---|---|---|
| Q1 | Phạm vi đợt coding | **P0 + spike toolkit** (port UI để đợt sau) |
| Q2 | Chính sách "đóng GUI = dừng server" | **Bỏ hẳn** — daemon sống độc lập, Discord vẫn push |
| Q3 | Console trong GUI mới | **Giữ nguyên full parity**: ring 1000 dòng, màu log level, chọn/copy từng đoạn, chịu burst 2000 dòng/s |
| Q4 | Toolkit spike | **Cả 3**: Slint (`winit-software`), iced (`tiny-skia`), gtk4-rs (TextView + cairo) |
| Q5 | Ngân sách RAM GUI (PSS toàn cây) | **< 60 MB** — chốt chính thức sau spike |
| Q6 | Mức chi tiết plan | **Task-level**: file, việc, acceptance criteria, effort, dependency |
| Q7 | Phân công | **Agent làm spike** (3 mini-app song song); GLM review code + kiểm chứng số đo; P0 do GLM viết chính |
| Q8 | **Chính sách repo sạch** (user bổ sung khi duyệt Phase A) | Repo GitHub Minewrap **chỉ chứa**: tài liệu, code app, build script build-from-source. **Cấm commit** tool chẩn đoán / memtest / spike / test ngoài lề app vào repo. Harness + spike + kết quả đo lưu riêng trên máy user tại `~/dev-memtest/` (bản gốc/master: archive repo GLM `tools/memtest/`, `spikes/`) |

---

## 1. MỤC TIÊU & KPI NGHIỆM THU

### 1.1 Mục tiêu

Đưa RAM của Minewrap từ **~196 MiB PSS (cây GUI Tauri/WebKit)** xuống: (a) khi không mở GUI — chỉ còn daemon ~6–8 MiB PSS; (b) sau P1 (đợt sau) — GUI Rust thuần < 60 MiB PSS. Đợt này hoàn thành (a) và cung cấp bằng chứng đo để chọn toolkit cho (b).

### 1.2 KPI (đo bằng harness `~/dev-memtest/` trên máy user — NGOÀI repo Minewrap, cùng phương pháp báo cáo v1.9.3 §12)

| KPI | Chỉ số | Ngưỡng pass |
|---|---|---|
| K1 | PSS toàn bộ wrapper khi **đóng GUI**, 1 server đang chạy + 1 WS console client + Discord service | **≤ 8 MiB** (baseline tương đương ~196 MiB nếu tính cả GUI) |
| K2 | PSS cây GUI khi mở (P0, vẫn WebKit) | không tệ hơn baseline +5% (≈ ≤ 206 MiB) — P0 không nhằm giảm phần này |
| K3 | Tests | 47 tests cũ pass + tests mới (state keeper, poller, discord service, REST CRUD) — mục tiêu **≥ 60 tests**, `warning = deny` giữ nguyên |
| K4 | Spike report | 3 toolkit × 3 kịch bản (idle / burst / stream) × 3 runs, median [min–max], kèm cold-start, binary size, LOC, build time |
| K5 | Frontend | `pnpm run check` 0 errors — **UI Svelte không đổi** trong P0 (IPC contract giữ nguyên) |

### 1.3 Định nghĩa hoàn thành

- **P0 done** = mọi task B1–B9 pass AC + demo end-to-end trên máy user (mở GUI → daemon tự dậy → start server → đóng GUI → server vẫn chạy, Discord vẫn push, mở lại GUI → reconnect + backfill log không gap) + số đo K1/K2 ghi vào `~/dev-memtest/results/` (lưu riêng ngoài repo — Q8; bản sao archive repo).
- **Spike done** = bảng so sánh C5 + khuyến nghị toolkit + khuyến nghị ngân sách chính thức + xác minh license, user duyệt.

---

## 2. HIỆN TRẠNG XÁC MINH TỪ CODE (khảo sát trực tiếp 2026-11-11)

### 2.1 Khớp với báo cáo v1.9.3

Workspace 4 crate (core 3.643 LOC / daemon 881 / remote 351 / tauri 1.648) + UI Svelte 3.505 LOC; edition 2024, `warnings = deny`, release `lto/codegen-units=1/strip`; ring log 500 (daemon) / 1000 (UI, `DEFAULT_RING`); EventBus bounded 256; WS console backfill 200; batch 100 dòng/40 ms; token 0600; AppImage bundle kèm sidecar `binaries/minewrapd` (`externalBin`); systemd user unit có sẵn.

### 2.2 NĂM GAP MỚI PHÁT HIỆN (ngoài báo cáo — ảnh hưởng trực tiếp P0)

| # | Gap | Bằng chứng (file:dòng) | Hệ quả với P0 |
|---|---|---|---|
| G1 | **Discord push chỉ chạy trong GUI forwarder** — đóng GUI là mất thông báo. Mỗi lần push tạo `reqwest::Client::new()`. Config `interval_seconds` (600 s), `first_push_delay_seconds`, `state_change_debounce_seconds` **tồn tại nhưng không có loop nào dùng** | `src-tauri/src/main.rs:149-194`; `config.rs:327-350`; grep toàn repo: 0 loop dùng interval | Phải dựng Discord service trong daemon (B3), không chỉ "chuyển" |
| G2 | **Daemon REST snapshot stale** — không có lời gọi `update_process`/`update_probe` nào trong minewrapd; `GET /instances` luôn trả offline/probe rỗng | grep: chỉ poller.rs định nghĩa + node_service.rs:346,790 gọi (phía GUI) | Daemon cần state keeper (B1) + poller (B2) thì GUI-as-client mới có dữ liệu đúng |
| G3 | **SLP probe chết ở runtime**: `register_probe` 0 caller, `Poller` 0 instance; App.svelte poll `get_snapshot` mỗi 2 s nhưng lệnh này không probe | `App.svelte:122`; `commands.rs:60-66`; `poller.rs:469-493` | Poller nền trong daemon (B2) đồng thời "hồi sinh" tính năng players/latency/MOTD |
| G4 | **Remote node là stub**: `remote_credentials()` trả "credential store not wired"; **10/22 command bỏ qua `node_id`** (`_node_id`: properties, mods, config, add/remove instance, discord_test…); `events_connect`/`console_connect` **0 caller** → remote không có log stream/sự kiện | `node_service.rs:258-262`; `commands.rs:124-263`; grep events_connect | P0 = hoàn thiện đường remote cho đủ 22 command rồi mới bỏ core nhúng (B6) |
| G5 | **Daemon thiếu 4 route GUI cần**: POST `/instances` (create), DELETE `/instances/{id}`, detect Java, scan work-dir; WS `/events` đang **drop** event `LogLine` và `RestartLoop` | `api.rs:29-51,505-530` | Thêm route + mở rộng `/events` (B4) |

### 2.3 Xử lý danh sách tối ưu cũ (theo tài liệu phương án)

| Mục | Quyết định | Làm ở task |
|---|---|---|
| D1 `TOKIO_WORKER_THREADS` (systemd) | **Giữ** — rẻ, đo được −0,13 MiB + giảm threads 13→3 | B8 |
| D2 lazy per-instance runtime (+0,75 MiB/instance offline) | **Giữ bản lite** — chỉ spawn owner task khi autostart=true hoặc lần start đầu | B8 |
| D5 shared `reqwest::Client` | **Giữ** — đang viết lại Discord service thì làm luôn | B3 |
| D3 (ring chunked), D4 (EventBus 256→64), D6 (panic=abort) | **Bỏ** — mức KiB, không đáng noise | — |
| G1–G5 (GUI/webview) | **Bỏ** — vô nghĩa sau P1 (đợt sau thay WebKit) | — |
| G3 (forwarder workers 12→1–2) | **Ghép vào B7** vì đụng đúng chỗ đó | B7 |

---

## 3. KIẾN TRÚC ĐÍCH SAU P0

```
┌────────────────────────────────────────────────────────────┐
│ minewrapd (LUÔN SỐNG — systemd user unit hoặc GUI spawn)   │
│  · InstanceManager + ProcessManager (như cũ)               │
│  · MỚI state keeper: subscribe bus → update InstanceState  │
│  · MỚI SLP poller nền (status_poll_interval, có sẵn cfg)   │
│  · MỚI Discord service (state-change + periodic 600 s      │
│    edit-in-place + debounce + shared reqwest Client)       │
│  · MỚI REST: POST /instances, DELETE /instances/{id},      │
│    GET /java, POST /scan-workdir                           │
│  · MỚI WS /events forward LogLine(kèm seq)+RestartLoop     │
│  · MỚI graceful SIGTERM (stop_all TERM→KILL rồi exit)      │
└───────────────▲────────────────────────────────────────────┘
                │ REST + WS (Bearer token, data_dir/token)
┌───────────────┴────────────────────────────────────────────┐
│ minewrap-tauri (GUI — mở khi cần, đóng = chỉ disconnect)   │
│  · NodeService = node registry: "local" = 127.0.0.1:port   │
│    + remotes (nodes.json 0600 — fix credential store)      │
│  · 22 command route qua RemoteClient (không còn core nhúng)│
│  · Forwarder: WS /events mỗi node → logs:batch/state:...   │
│  · Auto-spawn daemon detached (setsid) nếu /health fail    │
│  · Exit = đóng WS, KHÔNG stop server                       │
└───────────────▲────────────────────────────────────────────┘
                │ IPC (giữ nguyên contract — UI Svelte KHÔNG đổi)
┌───────────────┴──────────────┐
│ UI Svelte (frontend cũ)      │
└──────────────────────────────┘
```

Nguyên tắc bất biến: wire format API v1.0 **giữ nguyên** (chỉ additive → không bump version, `RemoteClient::health()` check `"1.0"` vẫn pass); token không bao giờ vào webview; `warning = deny`; mọi thay đổi có test.

---

## 4. PHASE A — BASELINE & HẠ TẦNG ĐO (0,5–1 ngày)

> Mục đích: bộ số đo "trước" đáng tin + công cụ đo dùng lại được cho P0 và mọi đợt sau. Số liệu phải đo **trên máy user** (Fedora 44, 12 lõi — cùng máy với báo cáo) thì mới so được với baseline.

**A1 — Port harness đo thành toolkit độc lập `~/dev-memtest/` (NGOÀI repo Minewrap — Q8)**
- *Vị trí:* working copy trên máy user `~/dev-memtest/`; bản gốc (master) trong archive repo GLM `tools/memtest/` — **không bao giờ commit vào repo Minewrap**. Toolkit tự chứa (không phụ thuộc repo app).
- *Files (mới):* `memsample.py`, `scenario.py`, `scenario_env.py`, `wsclient.py`, `configs/*.toml`, `fakejava` (stub bash in burst 2000 dòng → "Done" → stream 0,5 s/dòng), `run_baseline.sh`, `README.md`.
- *Việc:* tái tạo đúng thuật toán mô tả ở báo cáo §12.2: sampler duyệt cây process theo `PPid`, đọc `smaps_rollup` 1 Hz (RSS/PSS/USS/Swap + Threads/VmHWM), **loại subtree của stub** theo cmdline marker; runner spawn daemon release với port/data_dir riêng, đợi `/health`, chạy sampler N giây, xuất CSV; `wsclient.py` giữ 1 WS console + trả pong.
- *AC:* chạy S0 trên máy user cho số trong ngưỡng ±0,2 MiB so báo cáo (5,56 MiB RSS / 3,30 PSS); CSV đầy đủ cột như báo cáo.
- *Effort:* 0,25 ngày (GLM viết, agent chạy verify trên máy user).
- *Phụ thuộc:* không.

**A2 — Đo lại baseline đầy đủ (máy user, agent chạy theo protocol A1)**
- *Việc:* 6 kịch bản S0/S1/S3/SR/SW + GUI tree 30 s idle; ghi `~/dev-memtest/results/baseline-v1.9.3.md` (bảng median [min–max]).
- *AC:* chênh lệch mỗi kịch bản trong ngưỡng §15.4 của báo cáo (S0 ±0,2 … GUI ±10 MiB PSS). Nếu lệch lớn → dừng, tìm nguyên nhân môi trường trước khi làm P0.
- *Effort:* 0,25 ngày. *Phụ thuộc:* A1.

**A3 — Setup môi trường build**
- *Sandbox GLM:* cài rustup stable; `cargo test --workspace` (phần headless: core + daemon + remote) phải 47/47 pass; thử `apt-get install libwebkit2gtk-4.1-dev libsoup-3.0-dev` cho build GUI — nếu sandbox không dựng nổi thì build GUI qua agent trên máy user (code vẫn GLM viết, gửi patch base64 byte-exact).
- *Máy user (qua agent):* xác nhận cargo + pnpm + tauri CLI sẵn sàng (đã từng build v1.9.3).
- *AC:* cả hai môi trường build được; log test lưu `~/dev-memtest/results/env-check.md` (bản sao archive repo).
- *Effort:* 0,25 ngày. *Phụ thuộc:* không.

**A4 — Kiểm chứng bộ tool điều phối agent (đã có sẵn, không viết mới)**
- *Việc:* dùng `tools/` + `skills/SKILL-remote-opencode.md` trong archive repo (`oc.sh`, `oc_prompt.py`, `oc_report.py`, `rsh.sh`, `oc_fetch.py`); export `OC_URL`/`OC_AUTH`; tạo session spike-test, switch model `deepseek-v4.1-flash` (đã xác nhận còn active, 1M ctx), chạy 1 prompt echo kiểm tra toàn tuyến.
- *AC:* echo test trả kết quả đúng; model xác nhận trong session.
- *Effort:* 0,125 ngày. *Phụ thuộc:* không.

---

## 5. PHASE B — P0: DAEMON-FIRST (9 task, ước 4–6 ngày làm việc)

> Branch: `p0-daemon-first` (từ `main`). Mỗi task = ≥1 commit prefix `[B1]…[B9]`. STOP-gate: xong task → diff verbatim + output test → GLM review → mới sang task sau. Version đích: **v1.10.0**.

### B1 — Daemon state keeper (lấp gap G2)

- *Files:* `crates/minewrapd/src/instances.rs` (thêm method update), mới `crates/minewrapd/src/state_keeper.rs`, `crates/minewrapd/src/main.rs` (spawn task), `crates/minewrapd/src/lib.rs` (module).
- *Việc:* 1 tokio task subscribe bus wildcard; mỗi `Event::StateChange` → cập nhật `InstanceState` của instance tương ứng. **Port nguyên logic** `update_process_state` từ `node_service.rs:746-792` (giữ semantics last_error, started_at/stopped_at suy diễn, requested_stop) — đây chính là logic GUI đang chạy hôm nay, chỉ đổi chủ. Nâng cấp nhẹ (không bắt buộc): gán thêm `pid/uptime/restart_count/crash_count` thật nếu ProcessManager expose được qua OwnerHandle.
- *AC:* start server qua REST → `GET /api/v1/instances/{id}` chuyển "starting"→"online" đúng thời điểm; exit → "crashed"/"offline" đúng; unit test với bus giả (publish event → assert snapshot).
- *Effort:* 0,5 ngày. *Phụ thuộc:* không (làm đầu tiên).

### B2 — SLP poller nền trong daemon (lấp gap G3)

- *Files:* mới `crates/minewrapd/src/poller_task.rs`, `main.rs`/`instances.rs` (đăng ký).
- *Việc:* 1 task "status loop" chung (dễ quản lý add/remove instance hơn `Poller` per-instance): mỗi `status_poll_interval` (config sẵn, 15 s) — đọc danh sách instance + ProbeConfig từ InstanceManager → `probe_once` **song song** (join_all) → `InstanceState::update_probe`. Unresponsive phát sinh tự nhiên qua `combined_state()` (đủ `unresponsive_after_failures` lần fail). KHÔNG publish `StateChange` giả cho unresponsive (đó là derived state — UI thấy qua poll snapshot như hiện nay).
- *AC:* sau 2 lần probe fail (máy chủ không SLP) snapshot = "unresponsive"; SLP giả (python mini-server trả status JSON) → players/version/latency sống trong REST; ΔRSS daemon ≤ +0,3 MiB (đo S1 trước/sau); instance add/remove giữa chừng được vòng lặp nhặt đúng.
- *Effort:* 0,5 ngày. *Phụ thuộc:* B1 (InstanceState được cập nhật).

### B3 — Discord service trong daemon (lấp gap G1 + D5)

- *Files:* mới `crates/minewrapd/src/discord_service.rs`; `main.rs` (spawn); xoá khối Discord khỏi `src-tauri/src/main.rs:149-194`.
- *Việc:*
  1. **State-change push**: port logic GUI forwarder (state_change_posts + build_state_change_embed + push_status) vào 1 service subscribe bus; áp `state_change_debounce_seconds`.
  2. **Periodic push (mới, hồi sinh config chết)**: mỗi instance `enabled && webhook_set && đang online`: push đầu sau `first_push_delay_seconds`, rồi lặp mỗi `interval_seconds` (600 s); mode `edit-in-place` = PATCH vào message_id đã persist (`load_message_id/save_message_id` có sẵn), mode `new-message` = POST mới; **redact + strip_ansi như cũ**.
  3. **D5:** `static HTTP: OnceLock<reqwest::Client>` dùng chung toàn daemon (cả route `/discord/test`).
  4. Xoá `reqwest::Client::new()` từng call ở `api.rs:306` (discord_test).
- *AC:* đóng GUI → start/stop server → Discord vẫn nhận embed; message bị PATCH định kỳ đúng interval (test bằng webhook giả: python http server log request); spam-guard 429/5xx backoff giữ nguyên; ΔRSS sau 20 lần discord_test ≤ 0,1 MiB (D5 nghiệm thu).
- *Effort:* 1 ngày. *Phụ thuộc:* B1 (state snapshot cho embed).

### B4 — Mở rộng REST + WS /events (lấp gap G5)

- *Files:* `crates/minewrapd/src/api.rs` (routes + handlers), `crates/minewrapd/src/instances.rs` (method `add_instance`/`remove_instance` — port logic `NodeService::add_instance/remove_instance` incl. persist TOML), `crates/minewrap-remote/src/lib.rs` (client methods mới, làm ở B6).
- *Routes mới:*
  - `POST /api/v1/instances` — body JSON `InstanceConfig` → validate → spawn owner (lazy-safe) → persist → 201; trùng id → 409.
  - `DELETE /api/v1/instances/{id}` — stop graceful (TERM→KILL qua Control::Stop) → remove khỏi map + TOML → 200; không tồn tại → 404.
  - `GET /api/v1/java` — `detect_all()` (chỉ daemon làm, vì Java nằm cùng máy server).
  - `POST /api/v1/scan-workdir` — body `{work_dir}` → `scan_work_dir` + `report_work_dir` (giữ confinement như `commands.rs:275-306`).
- *WS /events sửa:* forward **đủ** event — `LogLine` (payload kèm `seq`, `ts`) và `RestartLoop` (hiện đang bị drop ở `api.rs:505-530`); gom batch server-side 100 dòng/40 ms theo đúng parity batch IPC hôm nay (giảm packet per-line).
- *AC:* curl CRUD instance pass; openapi sketch cập nhật; WS client test nhận log batch có seq liên tục qua burst 2000 dòng; API_VERSION **giữ "1.0"** (additive) — ghi chú PARITY.
- *Effort:* 1 ngày. *Phụ thuộc:* B1 (state cho snapshot sau add).

### B5 — Graceful shutdown daemon (SIGTERM)

- *Files:* `crates/minewrapd/src/main.rs`.
- *Việc:* tokio `signal` handler (feature đã có trong workspace deps): SIGTERM/SIGINT → gửi `Control::Stop` mọi instance → đợi tối đa `stop_timeout` (60 s, có sẵn config) → `Control::Shutdown` phần còn lại → exit 0. In log từng bước. Đây là đường "dừng hẳn mọi thứ" thay thế hành vi đóng-GUI cũ.
- *AC:* daemon đang chạy 1 server stub → `kill -TERM` → server nhận TERM, exit sạch, daemon exit 0 trong grace; systemd `stop` hoạt động đúng.
- *Effort:* 0,25 ngày. *Phụ thuộc:* không.

### B6 — GUI thành client thuần (lấp gap G4, bỏ core nhúng)

- *Files:* `src-tauri/Cargo.toml` (**bỏ dependency `minewrap-core`**, giữ `minewrap-remote`), `src-tauri/src/node_service.rs` (refactor lớn ~876 dòng → kiến trúc mới), `src-tauri/src/commands.rs` (10 command đang `_node_id` → routing thật), `src-tauri/src/types.rs`, `crates/minewrap-remote/src/lib.rs` + `types.rs` (bổ sung typed DTO + methods: `get_config`, `update_config`, `add_instance`, `remove_instance`, `detect_java`, `scan_launch`, `read/write_properties`, `list_mods`, `toggle_mod`).
- *Việc:*
  1. **Node registry file** `~/.config/minewrap/nodes.json` (0600): `[{id, name, url, token}]` — wire `remote_credentials()` (fix "not wired"): load/save, add/remove node qua command hiện có.
  2. **Node "local"**: `RemoteClient` trỏ `http://127.0.0.1:{port}` (đọc từ minewrap.toml GUI đang dùng — GUI vẫn load config để biết host/port/data_dir), token đọc từ `{data_dir}/token`. `is_local` vẫn true cho UI (icon/naming).
  3. **Routing 22 command**: một đường duy nhất qua RemoteClient; map REST `InstanceSnapshot` → `SnapshotDto` (giữ shape webview hôm nay); log backfill `?limit&since_seq` như cũ.
  4. Typed DTO dùng chung chuyển vào `minewrap-remote` (GUI không còn lấy type từ core).
- *AC:* `pnpm run check` 0 errors; **mọi màn hoạt động** khi daemon chạy local (list/snapshot/start/stop/command/logs/config CRUD/properties/mods/java/scan/discord test) — checklist thủ công 22 command; binary `minewrap-tauri` nhỏ đi (không link core) — ghi kích thước trước/sau.
- *Effort:* 1,5 ngày (task lớn nhất). *Phụ thuộc:* B4 (routes phải có trước).

### B7 — Auto-spawn daemon + exit = disconnect + forwarder WS

- *Files:* `src-tauri/src/main.rs` (chính), `node_service.rs` (forwarder), xoá dead-code `ensure_daemon_running`/`bundled_daemon_path` cũ.
- *Việc:*
  1. **Auto-spawn:** khi start GUI: probe `GET /health` (timeout 1 s). Fail → tìm `minewrapd` theo thứ tự: cạnh exe (AppImage `usr/bin`, `binaries/`) → `PATH` → spawn **detached**: `process_group(0)` (setsid), stdin `/dev/null`, stdout/stderr append `{data_dir}/daemon.log`, env `MINEWRAP_CONFIG=<config GUI dùng>`; đợi `/health` ≤ 10 s (poll 250 ms); fail → node local = Offline + thông báo lỗi rõ (không crash).
  2. **Exit:** XOÁ toàn bộ `ExitRequested` cleanup (`stop_all_local`, EXITING flag) — chỉ thoát. Comment chính sách mới ghi rõ lý do.
  3. **Forwarder:** mỗi node 1 kết nối WS `/events` (dùng `events_connect` có sẵn — viết caller đầu tiên cho nó); map message → emit `logs:batch` / `state:changed` / `nodes:changed` đúng payload shape IPC hôm nay (kèm `node_id`); reconnect + backfill `since_seq` khi rớt.
  4. **G3 (ghép):** bỏ thread dựng tokio multi-thread riêng — dùng `tauri::async_runtime` (worker vừa đủ); threads shell giảm.
- *AC:* (a) mở GUI khi daemon chưa chạy → daemon tự dậy + node Connected; (b) **đóng GUI khi 1 server đang chạy → server vẫn chạy, PSS daemon không đổi (±0,1 MiB), Discord vẫn push** (nghiệm thu K1); (c) mở lại GUI → reconnect, console backfill đủ không gap seq; (d) daemon chết giữa chừng → GUI hiện Offline + nút retry spawn.
- *Effort:* 1 ngày. *Phụ thuộc:* B6.

### B8 — systemd + D1 + D2-lite + deploy env

- *Files:* `packaging/minewrapd.service`, `crates/minewrapd/src/instances.rs` (lazy spawn), `packaging/appimage/AppRun` (giữ nguyên — `--daemon` đã có), `examples/minewrap.toml` (comment các giá trị mới).
- *Việc:*
  1. Service: thêm `Environment=TOKIO_WORKER_THREADS=2` (D1) + `Environment=MALLOC_ARENA_MAX=2` (best-practice deploy theo báo cáo §15.1); giữ `UMask=0077`, `Restart=on-failure`.
  2. D2-lite: `start_all()` chỉ spawn owner task cho `autostart = true`; instance còn lại giữ config trong map, owner spawn ở lần start đầu (port pattern `ensure_runtime` từ `node_service.rs:636-681` vào InstanceManager).
- *AC:* đo S3 (3 instance offline) sau đổi: RSS ≈ S0 + ≤ 0,2 MiB (bỏ +0,75×N MiB); threads daemon 3–5; kịch bản S1/SR/SW không regression so baseline (>±0,3 MiB → điều tra).
- *Effort:* 0,5 ngày. *Phụ thuộc:* B1–B4 xong (đo trên daemon hoàn chỉnh).

### B9 — Docs & parity & version + build script (Q8)

- *Files:* `ARCHITECTURE.md` (sơ đồ + chính sách mới: daemon-first, GUI = client, đường "dừng hẳn" = SIGTERM/systemctl), `README.md`, `docs/remote-access.md` (bổ sung: GUI giờ cũng là client — kiến trúc đồng nhất), `docs/RELEASE_NOTES.md` (v1.10.0: breaking — đóng GUI không dừng server; hướng dẫn migrate hành vi cũ: `systemctl --user stop minewrapd` hoặc `kill -TERM`), PARITY note API 1.0 additive, **`build.sh` (mới, root repo)**.
- *Việc (thêm theo Q8):* viết `build.sh` ở root — build từ source toàn phần (cài deps nếu thiếu → `cargo build --release` daemon + `pnpm install && pnpm tauri build` GUI), kèm `--daemon-only`. Rà soát repo trước release: **không chứa** tool chẩn đoán/memtest/spike (đã nằm ngoài theo Q8); unit-test cargo của app (K3) vẫn giữ trong repo vì là một phần code app.
- *AC:* docs mô tả đúng hành vi mới; release notes nêu rõ breaking change + đường lùi.
- *Effort:* 0,5 ngày. *Phụ thuộc:* B1–B8.

**Tổng effort Phase B: ~6,25 ngày** (nén còn 4–5 ngày nếu agent hỗ trợ chạy test/đo song song; timeline thực tế ~1 tuần làm việc).

---

## 6. PHASE C — SPIKE 3 TOOLKIT (2–3 ngày, chạy song song với B sau khi A1 xong)

> Thực hiện bởi **3 session OpenCode agent song song** (model `deepseek-v4.1-flash`), working copy code trên máy user `~/dev-memtest/spikes/{slint,iced,gtk4}/`, master đẩy vào archive repo `spikes/2026-11-toolkit/{slint,iced,gtk4}/` (GLM review qua diff verbatim — protocol STOP-gate) — **không đụng repo Minewrap** (Q8); **số đo chạy trên máy user** (cùng máy baseline) theo protocol C4 do GLM soạn. GLM tái đo ngẫu nhiên ≥1 kịch bản/toolkit để kiểm chứng (rule: không tin số chưa verify).

### C0 — Spec mini-app chung (GLM viết, đính kèm prompt agent)

Một app duy nhất, replicate đúng "hình thù" Minewrap hôm nay:

- **Cửa sổ:** 1280×800, dark theme, màu token lấy từ `ui/src/styles/tokens.css`.
- **Sidebar trái (220 px):** 5 instance giả (tên + badge trạng thái: online/offline/crashed/unresponsive) + footer trạng thái node.
- **Console (phần chính):** ring **đúng 1000 dòng** FIFO; mỗi dòng `[HH:MM:SS] [LEVEL] message`; LEVEL: INFO (mặc định), WARN (vàng), ERROR (đỏ), DEBUG (xanh) — tỉ lệ ~60/20/15/5; **bôi đen chọn + Ctrl+C copy được** (native selection — hard requirement Q3); auto-scroll stick-to-bottom, ngắt khi user kéo lên; chịu **burst 2000 dòng < 1 s** không khựng UI.
- **Form dưới console:** 2 text input + 1 select (4 option) + 1 button Apply (đổi name instance đang chọn — chứng minh state two-way).
- **Status bar đáy:** trạng thái + giờ + số dòng ring.
- **Generator dữ liệu (in-process, không network):** nút "Burst 2000", toggle "Stream 2 dòng/s", nút "Clear"; **CLI `--auto`** cho đo tự động: sau 10 s tự burst, sau đó stream 60 s.
- **Font:** Noto Sans 10 pt cả 3 app (fontconfig chung) — loại trừ biến số font.

### C1 — Slint spike
- Slint 1.x, backend `winit-software` (`SLINT_BACKEND=winit-software`); features: tắt `renderer-femtovg`, đo 2 cấu hình: **default** (accessibility on) và **tuned** (tắt `accessibility`). Console: `ListView` + `TextEdit`/text select — nếu selection không có sẵn, thử mô hình "LineEdit readonly nhiều dòng" hoặc custom — **ghi rõ kết quả thật, không bịa**.
- *Deliverable:* app chạy pass checklist C0 + bảng tính năng đạt/thiếu.

### C2 — iced spike
- iced 0.13 với renderer **tiny-skia** (CPU); console: thử `text_editor` (có selection native) VÀ variant "dòng text có màu trong column" — nếu text_editor không tô màu per-line được thì ghi trade-off thật.
- *Deliverable:* như C1.

### C3 — gtk4-rs spike
- gtk4-rs 0.9: `TextView` trong `ScrolledWindow` + `TextTag` màu (selection native sẵn); renderer cairo (mặc định, không GPU). Lưu ý: baseline GTK4 kéo libgtk — PSS là số thật trên máy đo.
- *Deliverable:* như C1.

### C4 — Protocol đo chuẩn (GLM soạn, agent thực thi trên máy user)

- **Hiển thị:** `Xvfb :99 -screen 0 1280x800x24` (đồng nhất, software path — đúng mục tiêu không GPU); xác nhận window mapped bằng `xwininfo`; screenshot `xwd` lưu làm bằng chứng.
- **Đo:** `~/dev-memtest/memsample.py` (từ A1) trên **cây process app**, 1 Hz.
- **Kịch bản mỗi app:** (1) idle 60 s; (2) burst: đo 30 s quanh thời điểm burst 2000 dòng; (3) stream 2 dòng/s trong 60 s. **3 runs/kịch bản**, báo cáo median [min–max].
- **Thêm:** cold-start (exec → frame đầu: instrument event-loop-ready + timestamp vào stderr + xác nhận bằng xwd); binary size (release, strip như workspace); build time; LOC; danh sách dependency hệ thống (ldd top-level).
- *AC:* jitter run-to-run ≤ 0,15 MiB; số ghi kèm environment (kernel, Xvfb, font, locale).

### C5 — Bảng so sánh + khuyến nghị (GLM tổng hợp)

Template bảng: PSS idle / burst / stream; USS; threads; cold-start; binary; LOC; build time; **license**; mức đạt checklist console (selection/copy/màu/1000 dòng/burst); ergonomics ghi chú.
**License check bắt buộc:** Minewrap là AGPL-3.0-only. iced & gtk4-rs = MIT (an toàn). **Slint = GPLv3 / Royalty-Free / Commercial** — xác minh tính tương thích GPLv3-code trong project AGPL-3.0-only (FSF: hướng GPLv3 → AGPLv3 được phép kết hợp, nhưng phải ghi rõ điều kiện) + đọc kỹ Slint Royalty-Free License terms; kèm link nguồn trong report. Nếu chọn Slint mà license chưa yên tâm → escalate user quyết.

### C6 — Go/No-Go vs ngân sách

- PSS (idle & stream) **< 60 MB** → pass, đề xuất toolkit chấm điểm: (1) đạt budget thấp nhất, (2) đạt checklist console full, (3) license sạch, (4) effort port 12 component.
- Cả 3 vượt budget → phân tích nguyên nhân (font cache? framebuffer? toolkit overhead?), đề xuất: giảm yêu cầu (phản Q3 — cần user duyệt lại) hoặc phương án P2 (UI từ daemon mở bằng browser) làm đường lùi.

---

## 7. DEPENDENCY GRAPH & TIMELINE

```
Ngày 1      ── A1 ─┬─ A2 (máy user, agent)
                  ├─ A3 (song song)
                  └─ A4 (song song)
Ngày 2–3    ── B1 → B2 → B3 → B4 → B5   (GLM viết core/daemon, sandbox)
              C0 → C1 ∥ C2 ∥ C3          (agent làm 3 spike song song)
Ngày 4–5    ── B6 → B7                   (GLM; GUI build trên máy user)
              C4 (đo 3 spike) → C5
Ngày 6–7    ── B8 (đo nghiệm thu D1/D2) → B9 (docs)
              C6 → SPIKE REPORT → USER GATE 2 (chọn toolkit + ngân sách)
Cuối đợt    ── DEMO P0 end-to-end + số K1/K2/K3 → USER GATE 3 (merge v1.10.0)
```

- Tổng: **~1,5 tuần calendar**. Effort thuần: A ≈ 0,75 ngày; B ≈ 6,25 ngày; C ≈ 2,5 ngày (bên agent).
- Điểm dừng dành cho user: (1) duyệt plan này; (2) duyệt spike report + chọn toolkit; (3) duyệt merge v1.10.0.

---

## 8. RỦI RO & MITIGATE

| # | Rủi ro | Khả năng | Mitigate |
|---|---|---|---|
| R1 | Console **selection** không đạt ở Slint/iced (hard requirement Q3) | Trung bình | Spike chứng minh TRƯỚC khi chọn (checklist C0); nếu chỉ 1 toolkit đạt → chọn nó bất kể PSS hơi cao hơn trong budget; nếu 0 toolkit đạt → escalate user kèm bằng chứng + options (`iced_selection`, custom widget, hoặc nới yêu cầu) |
| R2 | Slint license (GPLv3) xung đột AGPL-3.0-only | Thấp | Xác minh C5 với nguồn; option Royalty-Free/Commercial của Slint; iced/gtk4-rs MIT là đường lùi sạch |
| R3 | Số đo Xvfb không đại diện máy thật (compositor/GPU) | Trung bình | Mục tiêu chính là software rendering nên Xvfb đúng chủ đích; ghi environment; tùy chọn đo thêm 1 lần trên session thật của user để đối chiếu |
| R4 | Breaking change exit-policy gây khó chịu cho user hiện tại | Chắc chắn xảy ra | v1.10.0 + RELEASE_NOTES nêu đậm; đường "dừng hẳn" = `systemctl --user stop minewrapd` / `kill -TERM` (B5 làm cho đường này sạch) |
| R5 | GUI và daemon dùng config khác nhau → token/data_dir lệch | Trung bình | GUI luôn spawn daemon với chính config nó load; health check + đối chiếu `data_dir` trước khi coi local là "cùng máy"; lệch → thông báo lỗi rõ, không tự kết nối nhầm |
| R6 | Port 8080 bị chiếm | Trung bình | Lỗi connect hiển thị rõ + hướng dẫn đổi `[daemon] port` trong minewrap.toml; cân nhắc default port riêng (vd 8377) khi release |
| R7 | Sandbox 2 lõi/4 GB không build nổi GUI (webkit deps) | Trung bình | Build GUI qua agent trên máy user (patch base64 byte-exact); sandbox chỉ core/daemon + tests |
| R8 | Agent tự ý mở rộng phạm vi / bịa kết quả (bài học archive) | Trung bình | Protocol sẵn có: design-first, numbered steps, STOP-gate, honesty clause "machine-verified vs unverified", transfer base64 |
| R9 | `InstanceManager` lock Mutex trong async context gây deadlock khi thêm poller/discord service | Thấp | Pattern đã có sẵn trong code (`send_control` drop guard trước await); review checklist nhắc riêng mục này |

---

## 9. OUT OF SCOPE (đợt này) & PREVIEW ĐỢT 2

**Không làm đợt này:** port 11 màn UI sang toolkit (P1 — chờ spike report + user chọn toolkit + ngân sách chốt); P2 (serve UI từ daemon mở bằng browser); TUI ratatui; G1–G5, D3, D4, D6; Windows/macOS.

**Preview đợt 2 (P1) — sẽ lên plan riêng sau gate 2:** port 12 component Svelte sang toolkit thắng cuộc (thứ tự đề xuất: Console → Dashboard → Settings/Wizard → Properties/Mods → Nodes/Notifications); token màu/font từ `tokens.css`; mục tiêu PSS < 60 MB chốt; xoá hoàn toàn WebKitGTK khỏi dependency.

---

## 10. QUY TRÌNH LÀM VIỆC & REVIEW GATES

1. **Git:** branch `p0-daemon-first` từ `main`; commit nhỏ theo task `[B#]`; spikes trong archive repo `spikes/2026-11-toolkit/`; merge về main chỉ sau USER GATE 3.
2. **Phân công:**
   - *GLM (sandbox):* viết toàn bộ code P0 (B1–B9) — build/test phần headless tại chỗ; GUI build nếu sandbox đủ, không thì gửi patch base64 qua agent.
   - *Agent (máy user, `deepseek-v4.1-flash`):* chạy harness đo (A2, C4), build + xác minh GUI (B6/B7 AC), viết 3 spike app (C1–C3) theo spec C0.
   - *User:* 3 review gates (plan — spike report — merge).
3. **STOP-gate mỗi task:** diff verbatim + output test + số đo (nếu có) → GLM review → mới tính done. Không bao giờ tin vào tuyên bố "đã xong" không kèm bằng chứng.
4. **Số đo:** mọi con số công bố phải từ harness `~/dev-memtest/` output; GLM tái đo ngẫu nhiên để kiểm chứng; gì chưa verify thì ghi "unverified". Repo Minewrap không chứa số đo/tool đo (Q8) — kết quả lưu `~/dev-memtest/results/` + archive repo.
5. **Bảo mật:** PAT/token chỉ qua env/prompt per-session (`tools/README.md` contract); không bao giờ vào commit/repo/output; 401 → dừng, báo cáo.
6. **Cập nhật archive:** cuối session cập nhật `knowledge/minewrap-state.md` + `lessons-learned.md` (theo update protocol sẵn có).

---

*Plan này dựa trên: khảo sát code trực tiếp @ bfde421 (2026-11-11), báo cáo kiến trúc v1.9.3, tài liệu phương án giảm RAM, và bộ tool/skill đã kiểm chứng trong archive repo. Mọi số baseline trích từ báo cáo sẽ được tái đo ở A2 trước khi dùng làm chuẩn so sánh.*

*Changelog v1.1 (2026-11-11): user duyệt Phase A kèm sửa đổi — (1) harness memtest & spike & kết quả đo KHÔNG commit vào repo Minewrap, lưu riêng `~/dev-memtest/` trên máy user, master ở archive repo GLM; (2) repo Minewrap thêm `build.sh` build-from-source (giao cho B9); (3) mọi tham chiếu `tools/memtest/` trong plan đổi sang `~/dev-memtest/` (ngoài repo).*
