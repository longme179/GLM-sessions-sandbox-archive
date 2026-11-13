# BÁO CÁO KIẾN TRÚC & PHÂN TÍCH MINWRAP v1.9.3

> Mã nguồn: `/home/kimhoanglong/dev-MC-server-Wrapper` — workspace Rust (edition 2024), license **AGPL-3.0-only**, version **1.9.3**.
> Báo cáo dành cho việc rà soát (review) toàn bộ mã nguồn: kiến trúc, logic từng module, hợp đồng API, cấu hình, và **phân tích bộ nhớ thực đo + phương án tối ưu bộ nhớ**.
> Phạm vi đo memory: **chỉ lượng RAM mà bản thân Minewrap chiếm giữ** (daemon/GUI) — RAM cấp cho tiến trình máy chủ Java (JVM) **không nằm trong phép đo**, kể cả khi instance đang chạy.

## Mục lục

1. [Tổng quan hệ sinh thái](#1-tổng-quan-hệ-sinh-thái)
2. [Kiến trúc tổng thể và luồng dữ liệu](#2-kiến-trúc-tổng-thể-và-luồng-dữ-liệu)
3. [Logic chi tiết từng module — minewrap-core](#3-logic-chi-tiết-từng-module--minewrap-core)
4. [Logic chi tiết từng module — minewrapd (daemon headless)](#4-logic-chi-tiết-từng-module--minewrapd-daemon-headless)
5. [Logic chi tiết từng module — minewrap-remote](#5-logic-chi-tiết-từng-module--minewrap-remote)
6. [Logic chi tiết từng module — src-tauri (GUI shell)](#6-logic-chi-tiết-từng-module--src-tauri-gui-shell)
7. [Logic chi tiết frontend Svelte](#7-logic-chi-tiết-frontend-svelte)
8. [Hợp đồng API REST + WebSocket](#8-hợp-đồng-api-rest--websocket)
9. [Cấu hình `minewrap.toml` — schema & giá trị mặc định](#9-cấu-hình-minewraptoml--schema--giá-trị-mặc-định)
10. [Đóng gói & vận hành](#10-đóng-gói--vận-hành)
11. [Trạng thái build/test hiện tại](#11-trạng-thái-buildtest-hiện-tại)
12. [Phương pháp đo bộ nhớ](#12-phương-pháp-đo-bộ-nhớ)
13. [Kết quả đo bộ nhớ thực tế](#13-kết-quả-đo-bộ-nhớ-thực-tế)
14. [Phân tích phân bổ bộ nhớ trong tiến trình](#14-phân-tích-phân-bổ-bộ-nhớ-trong-tiến-trình)
15. [Phương án tối ưu memory footprint](#15-phương-án-tối-ưu-memory-footprint)

---

## 1. Tổng quan hệ sinh thái

Minewrap là một **server wrapper/bảng điều khiển quản trị** cho máy chủ Minecraft (tương thích vanilla/Forge/NeoForge/Paper/Spigot): quản lý vòng đời tiến trình server, log pipeline, theo dõi trạng thái qua SLP (Server List Ping), Discord webhook, quản lý `server.properties`/`mods`, và giao diện quản trị **nhiều node** (một node cục bộ nhúng trong GUI + nhiều node từ xa chạy `minewrapd`).

Repo chia làm 4 crate + 1 frontend + tài liệu/đóng gói:

| Thành phần | Vai trò | Công nghệ | LOC |
|---|---|---|---|
| `crates/minewrap-core` | **Thư viện lõi Tauri-free**: vòng đời tiến trình (state machine), log pipeline (ring buffer, batch, rotate), EventBus, SLP probe, Discord notifier, quản lý server.properties/mods, thu thập Java runtime, detect jar launch | Rust (std + tokio + serde + regex + toml + chrono + reqwest) | 3.643 dòng |
| `crates/minewrapd` | **Daemon headless** REST + WebSocket (axum) cho node remote/luôn chạy nền; nhúng cùng `minewrap-core` | Rust (axum 0.8, tokio) | 881 dòng |
| `crates/minewrap-remote` | **Client reqwest/tokio-tungstenite** gọi API `minewrapd` từ GUI (node remote) | Rust (reqwest 0.12 + rustls, tungstenite 0.24) | 351 dòng |
| `src-tauri` (crate `minewrap-tauri`) | **GUI shell Tauri 2**: IPC commands/events, NodeService routing (local nhúng core / remote client) | Rust (tauri 2, tauri-plugin-dialog, tokio) | 1.648 dòng |
| `ui/` | Frontend Svelte 5 + TypeScript (Vite) | Svelte/TS | 3.505 dòng |
| `packaging/` (`build-linux.sh`, `AppRun`, `minewrapd.service`, `tauri.conf.json`) | AppImage, systemd unit, config Tauri | shell/bundle | — |
| `ARCHITECTURE.md`, `README.md`, `docs/*` | tài liệu kiến trúc/ứng hành | Markdown | — |

**Ba cách vận hành:**

1. **Desktop GUI**: chạy `minewrap-tauri` — GUI nhúng trực tiếp toàn bộ core trong tiến trình Rust; cố tình **không spawn sidecar daemon** (chính sách: "GUI exit = dừng mọi server, không để nền gì chạy").
2. **Node từ xa / máy luôn chạy (headless)**: chạy `minewrapd` (systemd hoặc AppImage headless); GUI chỉ làm client trỏ tới qua REST/WS. Daemon mặc định bind `127.0.0.1` — đường ra từ xa được tài liệu hoá là SSH port-forward (xem `docs/remote-access.md`).
3. **Đa node**: GUI quản nhiều node đồng thời — node `local` (nhúng core) + các node remote (qua `RemoteClient`), mỗi node giữ state riêng.

Cả hai runtime (GUI nhúng và daemon headless) phục vụ **cùng một hợp đồng REST/WS** (API v1.0) — đây là bản rewrite v2 của codebase Python v1, theo mục tiêu "parity" chủ đích: nhiều module Rust ghi chú port 1-1 từng file Python (`log_buffer.py`→`logs.rs`, `poller.py`→`poller.rs`, `events.py`→`events.rs`, `auth.py`→`auth.rs`, `instances.py`→`instances.rs`…).

**Bản dựng release (đo trên máy này, 2026-11-11):**

| Kind | File | Kích thước | Profile |
|---|---|---|---|
| daemon | `target/release/minewrapd` | 5.59 MiB | `lto = true`, `codegen-units = 1`, `strip = true` |
| GUI | `target/release/minewrap-tauri` | 10.39 MiB | tương tự (object tĩnh `libminewrap_tauri.a` ~163 MiB trước link) |

Workspace quy định chặt: `warning = deny` (linter bar, mọi warning là lỗi), edition 2024, dependency chuẩn hoá qua `[workspace.dependencies]` (tokio, serde, serde_json, regex, toml, chrono, reqwest).

---

## 2. Kiến trúc tổng thể và luồng dữ liệu

### 2.1 Sơ đồ khối

```
                ┌──────────────────────────────────────────────┐
                │              Svelte UI (webview)              │
                │ Dashboard / Console / Wizard / Settings / ...│
                │      ipc/factory → tauri.ts | mock.ts         │
                └───────────────▲──────────────────────────────┘
                                │ invoke() / listen()
                ┌───────────────┴──────────────────────────────┐
                │        src-tauri::minewrap-tauri (Rust)       │
                │  commands.rs → NodeService (routing)          │
                │  main.rs (forwarder: Event → "logs:batch",    │
                │                    "state:changed")           │
                └──────┬───────────────────────────┬───────────┘
                       │ local node (nhúng core)    │ remote node
                       ▼                            ▼
 ┌────────────────────────────────────────────────┐   ┌──────────────────────┐
 │ minewrap-core (ProcessManager per instance)    │   │ minewrap-remote      │
 │  · spawn/stop/escalation (TERM→KILL)           │   │  reqwest REST +      │
 │  · state machine offline→starting→online→      │◄──┤  tokio-tungstenite   │
 │    stopping→crashed + auto-restart backoff     │   │  WS client           │
 │  · LogBuffer ring (mặc định 500 dòng)          │   └──────────┬───────────┘
 │  · Notifier (Discord webhook, redact, retry)   │              │
 │  · Poller / SLP probe (protocol 47)            │              │
 │  · EventBus (topic pub/sub, bounded 256)       │              │
 └──────┬─────────────────────────────────────────┘              │
        │ cùng core, cùng hợp đồng API v1.0                      │
        ▼                                                        │
 ┌────────────────────────────────────────────────┐              │
 │ minewrapd (axum REST + WS trên host:port)      │◄─────────────┘
 │  TokenAuth (bearer, constant-time compare)     │
 │  InstanceManager (HashMap<String, Managed)     │
 │  /api/v1/* + /console/{id} + /events           │
 └────────────────────────────────────────────────┘
```

### 2.2 Luồng log (đường "hot")

1. **stdout server** được đọc bất đồng bộ bằng `tokio::process`; pipe giới hạn `PIPE_CAPACITY = 256` thông điệp; mỗi dòng tối đa `MAX_LINE_BYTES = 64 KiB` (vượt giới hạn sẽ cắt và thêm hậu tố "… [truncated]").
2. Mỗi dòng thu được: ghép `\r\n`/`\r`, decode UTF-8 kiểu lossy (không reject dòng lỗi), gắn timestamp và **seq tăng dần theo instance**, push vào **LogBuffer** (ring có capacity `log_buffer_lines`, mặc định **500** dòng/instance), đồng thời publish **event `LogLine`** lên EventBus.
3. Song song, dòng được nối ra **file** bằng `RotatingFile` (`log_max_bytes` mặc định 10 MiB, `log_backups` = 3: khi vượt size, rotate `log → log.1 → log.2 → log.3`, bỏ bản già nhất).
4. **Batcher** gom các dòng sẵn có thành `LogLineBatch` tối đa `BATCH_MAX_LINES = 100 dòng/batch`, interval `BATCH_INTERVAL_MS = 40 ms` — mục tiêu giảm allocation và gửi gói lớn thay vì từng dòng.
5. Người nhận:
   - **WS `/console/{id}`** (daemon): backfill **200 dòng** gần nhất ngay khi kết nối, rồi duy trì stream live.
   - **IPC GUI**: forwarder (subscribe bus của node local) emit `logs:batch`; frontend lưu ring riêng **1000 dòng** trong webview (`DEFAULT_RING` trong `stores/console.ts`), dedupe/ghép bằng `seq`.
6. **Hợp đồng seq**: tràn ring thì dòng già bị xóa; consumer kết nối lại dùng `since_seq` (REST `?since_seq=` hoặc đầu WS); **gap seq** ở phía consumer là cách phát hiện mất dòng (không che giấu — v1 parity chi tiết trong tests). Consumer chậm: mọi kênh EventBus là **bounded 256 với `try_send`** — đầy thì drop silent, ring buffer + seq bù lại.

### 2.3 State machine & auto-restart

```
offline ──start──▶ starting ──regex "Done (...s)! For help"──▶ online
                     │  (spawn process group riêng)               │
                     │  exit trước regex → crashed                │ stop → stopping (TERM)
                     ▼                                            ▼
                  crashed ◀──exit (exit_code)◀──────────────── stopping
                     │                                            │ exit → offline
                     │ policy = "on-crash"                        │
                     │ crash_count++ (≤ max_retries = 5)          ▼
                     └──▶ backoff (5s base, ×2^n, cap 300s) ──▶ starting
                 (reset_after = 600s; nếu còn crashed sau max_retries
                  → publish RestartLoop, dừng auto-restart)
```

- **Spawn**: `Command::new(java_path)` trực tiếp (không qua `sh -c`), `current_dir = work_dir`, args = `jvm_args ++ launch_args`; process được đặt vào **process group riêng** để stop có thể `kill` cả nhóm.
- **Stop escalation**: gửi **SIGTERM** cho process group → chờ `kill_grace_seconds` (mặc định **5 s**) → vẫn sống thì **SIGKILL** group.
- **Startup watchdog**: `startup_deadline = now + startup_timeout` (**300 s**); quá deadline chưa thấy "Done" → chuyển **Crashed** với reason `startup_timeout`, thực hiện TERM rồi KILL theo cùng escalation.
- **Requested-stop vs crash**: người dùng chủ động Stop → trạng thái cuối là **Offline** (`requested_stop = true`); tự thoát không do stop → **Crashed** → policy quyết định auto-restart (`"never"` | `"on-crash"`).
- **"Unresponsive"** không sống ở ProcessManager mà ở tầng merged state (poller): số probe fail liên tiếp ≥ `unresponsive_after_failures` (mặc định **2**) trong khi process đang `online` → `combined_state = "unresponsive"`.

### 2.4 Command & Control path

Mọi y lệnh điều khiển đi qua **channel bounded gồm enum `Control`**: `Start` / `Stop` / `SendCommand(String)` (ghi dòng + `\n` vào **stdin** của server) / `ApplyConfig(InstanceConfig)` (hoán đổi nội config giữa các lần start) / `Shutdown`.

- **REST** (daemon): handler → `InstanceManager::send_control(id, ctrl)` → `tokio::spawn` send qua `ctrl_tx` (không block event loop khi channel đầy).
- **GUI**: command `instance_start/…/send_command` → `NodeService` — local: đi thẳng handle nhúng; remote: POST tương đương lên daemon.

### 2.5 Events & hiển thị

- **EventBus** topic = `instance_id`, có **wildcard `*`**. Payload enum sealed với serde tag `"kind"`: `state_change {instance_id, old_state, new_state, reason}` / `restart_loop {instance_id, crash_count}` / `log_line {instance_id, line}`.
- **WS `/events`** (daemon): wildcard subscriber nhận mọi topic; GUI kết nối qua `RemoteClient::events_ws_url`.
- **GUI nhúng core**: `spawn_forwarder_future` subscribe bus trực tiếp; gom `LogLine` theo instance (kết dính lines thành batch, giữ first_seq/last_seq) rồi `emit "logs:batch"`; với `StateChange` → emit `state:changed`. Payload shape cố ý khớp wire format của `minewrapd` (parity, theo PARITY.md) nên Adapter lớp UI không phân biệt local/remote.

### 2.6 Bảo mật & xác thực

- **Bearer token**: 32 byte random từ `/dev/urandom` (hex 64 ký tự). Thứ tự: env `MINEWRAP_TOKEN` → file `data_dir/token` đã tồn tại → sinh mới: ghi `.token.tmp`, chmod **0600**, rename; lần sinh đầu in ra stdout **một lần duy nhất**.
- Verify bằng **so sánh thời gian hằng (constant-time)** byte-wise, không early-exit (parity `hmac.compare_digest` của v1).
- Token **không bao giờ vào webview**: Rust giữ token (keyring/file); UI chỉ biết `node_id`. Mọi route trừ `/health` đều cần bearer; **WS handshake bị từ chối trước `accept`** (trả 401 ngay trong handler trước khi upgrade).
- **Confinement path**: mọi thao tác file (properties/mods) đi qua `confine_path()` — canonicalize + chắc chắn nằm trong instance dir; mod name cấm chứa `/` và `\`.

---

## 3. Logic chi tiết từng module — minewrap-core

> Toàn bộ 12 file `.rs` của crate, xếp theo vai trò; 3.643 LOC; **45 test unit** nằm inline `#[cfg(test)]`.

### 3.1 `lib.rs` (50 dòng)
Cổng công khai của crate: re-export các kiểu chính (`DaemonConfig`, `InstanceConfig`, `Notifier`, `EventBus`, `Poller`/`probe_once`, `ProcessManager`/`Control`, `LogBuffer`/`RotatingFile`, `ModEntry`/`list_mods`, `PropertiesDocument`, `JavaRuntime`/`detect_all`, `LaunchCandidate`/`inspect_jar`…). Định nghĩa 2 hằng phiên bản: `API_VERSION = "1.0"` (hợp đồng REST/WS — `/health` trả field này, GUI kiểm tra khớp khi kết nối) và `CORE_VERSION` (lấy `CARGO_PKG_VERSION`). Có 1 test metadata.

### 3.2 `config.rs` (870 dòng) — schema cấu hình TOML
Bộ struct chính:

- **`DaemonConfig`** — toàn file `minewrap.toml`: `daemon: DaemonSettings` + `instances: Vec<InstanceConfig>`.
  - `DaemonSettings` (mặc định): `host` = `"127.0.0.1"`, `port` = 8080, `data_dir` = `"./data"`, `status_poll_interval` = 15.0 s, `unresponsive_after_failures` = 2, `defaults: InstanceDefaults`.
  - `InstanceDefaults` (mặc định): `startup_timeout` = 300.0 s, `stop_timeout` = 60.0 s, `kill_grace_seconds` = 5.0 s, `done_regex` = `Done \(\d+(\.\d+)?s\)! For help` (compilable), `log_buffer_lines` = 500, `log_max_bytes` = 10 MiB, `log_backups` = 3.
- **`InstanceConfig`** — per-server: `id` (slug unique — map key + bus topic), `name`, `work_dir`, `java_path`, `jvm_args[]`, `launch_args[]`, `autostart`, `probe {host, port, timeout}`, `restart {…}`, `discord {…}`; `display_name()` fallback về id; mỗi instance fallback phần thiếu về `defaults` của daemon.
- **`RestartConfig`**: `policy` (`"never"` | `"on-crash"`, mặc định **on-crash**), `max_retries` = 5, `backoff_base_seconds` = 5.0, `backoff_max_seconds` = 300.0, `reset_after` = 600.0 s.
- **`DiscordConfig`**: `webhook_url` (secret — Serialize chỉ xuất `webhook_set: bool`), `enabled_events`, `max_log_chars` (mặc định 1500, validate ≤ 4096).
- **`ProbeConfig`**: `host` = 127.0.0.1, `port` = 25565, `timeout` = 3.0 s.

Các thao tác:

- `load_from / save_to` — parse/serialize TOML full-file; thiếu field dùng default.
- **`validate()`** — kiểm phạm vi từng field (`*interval/timeout ≥ 0.1`, `log_buffer_lines ≥ 10`, `log_backups ≤ 20`, regex phải compile, policy thuộc tập cho phép, webhook rỗng = disabled v.v.).
- **`patch_instance(id, JSON)`** — update runtime: nhận serde_json object; từng field (name/work_dir/java_path/jvm_args/launch_args/autostart/probe.host/probe.port/probe.timeout/restart.policy/restart.max_retries/restart.backoff_*/restart.reset_after/discord.*) được validate & gán riêng (không field lạ), rồi persist TOML (nếu daemon có `config_path`). Được dùng chung bởi REST `PUT /api/v1/instances/{id}/config` và GUI command `update_config`.

### 3.3 `process.rs` (684 dòng) — vòng đời tiến trình, trọng tâm crate
- Hằng: `MAX_LINE_BYTES = 64 KiB`, `PIPE_CAPACITY = 256` (channel), `BATCH_INTERVAL_MS = 40`, `BATCH_MAX_LINES = 100`; libc SIGTERM/SIGKILL.
- **`ProcessManager::new()`** tạo trạng thái per-instance nhưng **không spawn task** cho tới `.spawn()`; `.spawn()` khởi chạy **owner loop** (tokio task chính, trả `OwnerHandle {ctrl_tx, …}`) — select giữa: (1) `Control` từ channel, (2) `child.wait()` (exit), (3) line stream từ `spawn_reader`, (4) deadline timers (startup watchdog; TERM→KILL grace).
- **`spawn_server()`** — `tokio::process::Command` chạy `java_path` với args `jvm_args ++ launch_args`; `current_dir(work_dir)`; đặt **process group riêng** (không shell, không đụng env). Trả về hợp đồng `spawn_reader` đảm nuôi đọc stdout.
- **`spawn_reader()`** — `tokio::spawn` một task `read_until(b'\n')` độc lập; normalize `\r\n`/`\r`, decode UTF-8 lossy, cut theo `MAX_LINE_BYTES` rồi đẩy qua mpsc.
- **Owner loop — handler `Control`**:
  - `Start` → spawn server, state `Starting`, `startup_deadline` = now + startup_timeout; ghi banner từ Minewrap vào ring.
  - Một line khớp `done_regex` → `Online` (xóa deadline, publish StateChange online). Trong runtime thật, regex được compile từ config (custom được).
  - Exit khi đang Starting → **Crashed** + reason `exit_before_done` & exit_code; exit khi đang Online → **Stopping → Offline** với `stopped_at`.
  - `Stop` → TERM; nếu còn sống sau `stop_timeout` (60 s) → theo escalation (`kill_grace_seconds`) → KILL. `forced_stop` đánh dấu stop khi đang Starting (xử lý "chưa Done vẫn được dừng").
  - Startup watchdog quá hạn → transition `Crashed`, reason `startup_timeout`, TERM → sau `kill_grace_seconds` vẫn sống thì KILL (các check timer ở owner loop).
- **Auto-restart (policy `on-crash`)**: sau crash (không phải stop theo yêu cầu của người dùng), `crash_count += 1`; nếu uptime gần nhất ≥ `reset_after` → reset counter về 0; nếu `crash_count ≤ max_retries` → delay `min(base × 2^(n−1), max)` rồi tự Start lại (banner auto-restart #n); nếu vượt → publish **RestartLoop** event (UI/Discord sẽ thông báo "đã dừng auto").
- **Mọi line** (kể cả banner của wrapper) đi qua: `LogBuffer::append` (seq tự tăng trơn) → publish `Event::LogLine` → `RotatingFile` write theo cấu hình.
- `ProcessStatus` — snapshot `state/pid/started_at/uptime/restart_count/crash_count/exit_code/requested_stop/forced_stop` dùng cho merged-state & UI.

### 3.4 `logs.rs` (339 dòng)
- `LogLine {seq: u64, ts: DateTime<Utc>, line: String}`; `parse_line()` trim `\r\n`/`\r`, UTF-8 lossy; truncate khi vượt `MAX_LINE_BYTES` (+ "… [truncated]").
- **`LogBuffer`** — ring bằng `VecDeque<LogLine>`: `append(line, ts)` auto tăng `seq` (1-based, monotonic), evict oldest khi đầy; `tail(n)` lấy N gần nhất; `since(seq)` trả các dòng sau seq (dùng cho gap-recovery); `last_seq()` cho UI.
- **`Batcher`** — bọc mpsc receiver; `drain_pending()` dùng `try_recv` loop để gom tới `max_lines`; `take_batch()` lấy hết pending thành `LogLineBatch {first_seq, last_seq, lines}`. ProcessManager hiện dùng `BATCH_*` qua select interval (batching inline); Batch giữ cho các đường pipeline tách sau (forwarder GUI etc.).
- **`RotatingFile`** — append-only bằng koji `std::fs::OpenOptions::append()`; khi size vượt `max_bytes` (mặc định 10 MiB), rotate theo chuỗi `log → log.1 → … → log.N` (giữ `backups`), xóa bản ngoài giới hạn; write-through sync (std) trên trường nhật; global open file handle per instance.

### 3.5 `discord.rs` (481 dòng)
- Hiện yêu cầu bảo mật: `mask_webhook_url()` — mask token từ URL (client-side display & log); `redact_line()` — lọc token/password (mặc command không nhận chuỗi secret; tự scan regex) trước khi nhét vào embed; `strip_ansi()` — Discord không hiển thị ANSI escape của terminal.
- **`build_status_embed` / `build_state_change_embed`** — tạo embed Discord màu theo trạng thái (start/stop/crash/restart-loop), title + description tóm tắt, **tối đa `max_log_chars` ký tự log gần nhất** (tail), footer với `humanize uptime` (xem `humanize_uptime()`).
- **`Notifier`** — giữ `DiscordConfig` + `reqwest::Client` + `state_dir/instance_id` cho **edit-in-place**: file message_id được persist (`load_message_id/save_message_id`) — stop/crash sẽ **PATCH** (edit) của Discord start-message ban đầu (không spam channel thêm).
- **`request()`** — HTTP wrapper có **429 `retry_after` capped**, **5xx backoff**, timeout cứng (v1 parity: `mcstatus Prober` sẽ không nhồi nhét); `push_status()` push status-change có filter theo `enabled_events` + `max_log_chars` tail; `send_test()` — gửi embed test từ fake snapshot (trả `DiscordTestResult {ok, error}` cho REST `/discord/test`).

### 3.6 `events.rs` (217 dòng)
- EventBus topic pub/sub + wildcard (đã mô tả §2.5): channels bounded 256, `try_send` — slow consumer drops oldest, seq-gap để recover; 4 tests chủ đề/wildcard/bound/gap.

### 3.7 `java.rs` (323 dòng)
- **`JavaRuntime`** — `home / binary / major / full_version / vendor / arch / source / is_jdk`; Serialize tay (path → string).
- **`detect_all()`** — quét theo thứ tự ưu tiên: `JAVA_HOME` → `java` chỉ định PATH (which && resolve symlink) → `/usr/lib/jvm` → `~/.jdks` → SDKMAN (`~/.sdkman/candidates/java`); dedupe theo canonical home; comment cho phép thêm nguồn asdf/mise/jenv khi cần.
- **Parse `release` file** không cần subprocess: đọc key `JAVA_VERSION`, `IMPLEMENTOR*/IMPLEMENTOR_VERSION`, `OS_ARCH`; `is_jdk` (bin/javac tồn tại hoặc key `JDK_VERSION`). Fallback `runtime_at`: chạy `<home>/bin/java -version` (arg trực tiếp, timeout 2 s) và parse stderr.
- `parse_major()` — hỗ trợ cả "1.8.0_452" (đọc cleaned "8") và "21.0.2" ("21").
- `min_java_for_minecraft()` — bảng ánh xạ phiên bản Minecraft → Java major tối thiểu (vd. 1.20.5+ → 21; 1.17+ → 17; pre-1.17.5 → 8) — dùng UI báo pick/hint; số cứng trong bảng, v1 parity.

### 3.8 `launch.rs` (365 dòng)
- **`scan_work_dir(dir)`** — liệt kê entry: `*.jar` → `LaunchKind::Jar`; `run.sh`/`*.sh` → `Script`; `user_jvm_args.txt`/`unix_args.txt` → `ArgsFile`; mở rộng quét sâu `libraries/**` (tối đa 3 cấp) để tìm `unix_args.txt` (Forge/NeoForge); mỗi candidate gợi ý `suggested_launch_args` (`-jar … nogui`, `@user_jvm_args.txt @libraries/… nogui`, `./run.sh nogui`). Confinement: scan bên trong canonical work dir — không gọi shell.
- **`inspect_jar(jar)`** — đọc **ZIP central directory bằng pure std** (không shell/unzip): quét EOCD `PK\x05\x06`, loop `PK\x01\x02` tìm entry `version.json` (chỉ nhận **Stored — method 0**), đọc nội dung rồi parse `"id"`/`"name"` best-effort (`extract_json_string`).
  - type guess: chữ "forge"/"neoforge"/"paper"/"spigot" trong name → tương ứng; có `id` → "Vanilla"; `mc_version` từ `id` (chấp nhận cả `1.21.1-…-server`).
  - cộng `min_java` qua `min_java_for_minecraft`.
- **`suggested_for_mode(mode, work_dir, jar)`** — 3 mode: `"jar"` / `"args-file"` / `"custom"` cho Wizard lleva determinism; **`report_work_dir(dir)`** — report liveness: exists/readable/**writable (thử write file marker)**/has_server_properties/has_eula/has_world/has_mods + jar_candidates + notes (chưa eula, chưa properties, không writable) — UI Wizard hiển thị ngay.

### 3.9 `mods.rs` (125 dòng)
- `list_mods(instance_dir)` — tạo `mods/` nếu thiếu; liệt kê `.jar` (enabled) & `.jar.disabled` (disabled) + size; sort theo tên.
- `toggle_mod(dir, name)` — rename `.jar ↔ .jar.disabled`; **confinement cứng**: name cấm separator, dir canonicalize + confine-path trước rename; trả về enabled mới cho UI.
- `format_size()` — B → KiB → MiB → GiB (humanize).

### 3.10 `properties.rs` (212 dòng)
- **`PropertiesDocument`** — parser giữ-format: mỗi dòng thành `Empty` / `Comment` / `Property {key, value, group}` / `Raw` — **round-trip byte-identical cho dòng không bị chạm** (không sort lại, không đụng whitespace); render luôn `\n`.
- `get(key)` scan; `set(key, value)` gọi `validate_property` (bảng per-key: kiểu/range/charset các key Minecraft rồi; key lạ giữ nguyên) cho cả typed access.
- **`confine_path(root, rel)`** — canonicalize + kiểm prefix; mọi path trỏ vào instance dir phải qua hàm này. `properties_path()` trả `server.properties`.

### 3.11 `poller.rs` (495 dòng)
- **SLP (ADR-1, hand-rolled)** — protocol 47: `varint()`/`read_varint()` (guard "varint too long"); `packet()` length-prefixed; `request_status(host, port, timeout)` — TcpStream tự timeout, handshake (next-state 1) + status request; đọc có **cap 64 KiB** (`MAX_PACKET`), biến chuỗi; `parse_status_json()` — `version.name`, `players.online/max/sample`, và **MOTD extract** (string | chat-object `{text, extra[]}` | array) dạng lossy; `probe_once(config)` — đo `latency_ms`, `checked_at`, lỗi được kiểu hoá (connect/write/read/parse).
- **`InstanceState`** — merged model (v1): process (`ProcessStatus`) + probe (`ProbeInfo`); `failures` tăng khi probe fail; `combined_state()` → 5 trạng thái + `"unresponsive"` (process online mà failures ≥ `unresponsive_after_failures`); `summary()` & `snapshot()` phục vụ REST/WS/UI.
- **`Poller`** — helper struct (diễn giải v1) nhưng ở runtime v1.9.3 **poll ngược dồn lại phía UI/API gọi** (không có background poll loop trong daemon — grep đã xác nhận) — UI Dashboard tự interval gọi REST snapshot khi cần.

### 3.12 `discard.rs` (7 dòng)
Placeholder giữ module cho kế hoạch chia crate (core không được phụ thuộc web framework) — không logic.

---

## 4. Logic chi tiết từng module — minewrapd (daemon headless)

### 4.1 `main.rs` (61 dòng)
Điểm vào: đọc `MINEWRAP_CONFIG` (mặc định `minewrap.toml` CWD); fail-soft (load lỗi → dùng defaults & cảnh báo). Phần token như §2.6. Tạo `EventBus` → `InstanceManager::load(config, bus, config_path)` (**`start_all()` tự chạy**: mỗi instance spawn ProcessManager owner ngay từ boot). `create_router(mgr, auth)` → `TcpListener::bind(host:port)` → `axum::serve`. In banner "listening on {addr} (SSH forward to reach remotely)".

### 4.2 `lib.rs` (11 dòng)
Cổng crate: `pub mod api/auth/instances`; re-export `create_router`, `ws`, `InstanceManager`.

### 4.3 `api.rs` (531 dòng)
- **`create_router(manager, auth)`** — khai toàn bộ surface (bảng §8) + Extension chung `(Arc<InstanceManager>, TokenAuth)`; middleware bearer cho mọi route trừ `/health`; JSON error envelope `{detail}` 401/404/409/422.
- Creatures: handlers gọn — parse path/params → gọi `InstanceManager` hoặc core trực tiếp cho phần stateless (properties/mods). `PUT /instances/{id}/config` → `mgr.patch_instance` (validate + persist + ApplyConfig live).
- **`POST /instances/{id}/discord/test`** — dựng fake snapshot (`state = online`), tạo `Notifier::new(cfg, reqwest::Client::new(), mgr.data_dir()/discord, id)` → `send_test` → JSON result.
- **WS handlers** (nằm đây để router tập trung; logic implementation ở `handle_console`/`handle_events`): `console_ws` — check token ở **handshake** (Authorization header), nếu sai trả 401 trước `accept`; khi vào: backfill 200 dòng + snapshot (hello + snapshot messages) rồi live loop; client → daemon chỉ hiểu `{"type":"command","command":"…"}` → đẩy `Control::SendCommand` + confirm `{"type":"command_result","accepted":true}`; close sạch khi client đóng.
- Hằng `API_VERSION = minewrap_core::API_VERSION` — hợp đồng ở 1 mức cao.

### 4.4 `auth.rs` (78 dòng)
- `TokenAuth { token }` — `verify` dùng **so sánh thời gian hằng byte-wise** (parity `hmac.compare_digest`); `generate()` 32 byte từ `/dev/urandom` → hex.
- `bearer_from_header("Bearer abc") → Option<String>` (nới space).
- 2 tests (`verify_rejects_wrong_and_missing`, `bearer_parses`).

### 4.5 `instances.rs` (238 dòng)
`InstanceManager`:

- `load()` + **`start_all()`** — mỗi `InstanceConfig` tạo `LogBuffer(defaults.log_buffer_lines)` shared + `ProcessManager::new().spawn()` (OwnerHandle) + `InstanceState` (`unresponsive_after_failures` từ config). Kéo theo: **mỗi instance luôn có owner task & ring buffer ngay từ boot** (kiến trúc "always-on manager"), kể cả chưa được start lần nào.
- Toolkit đọc: `count/ids/config_of/summary_of/snapshot_of/backfill(id, limit, since_seq)` — backfill: nếu `since` có dữ liệu dùng `since`, nếu trống thì `tail(limit)` (ưu tiên gap-recovery).
- `patch_instance(id, JSON-doc)` — merge JSON → core validate → cập nhật memory map + persist TOML (nếu `config_path`) + gửi `Control::ApplyConfig` tới owner (live-swap cho start kế tiếp).
- `send_control(id, ctrl)` — lấy `ctrl_tx` từ handle, `tokio::spawn` send; không block thread handler khi channel đầy.
- `subscribe(topic)` / `bus()` — bridge cho WS handlers.
- `under_data_dir()` — helper absolute/relative; đốt đáp cho discord state path.

---

## 5. Logic chi tiết từng module — minewrap-remote

### 5.1 `lib.rs` (233 dòng)
`RemoteClient { http: reqwest::Client, base, token }` — một reqwest client để dùng chung TLS pool; `base` là `http://host:port`; **mọi request thêm `Authorization: Bearer <token>`**.

- `health()` — GET `/health` (public, không auth), **cứng yêu cầu `api_version == "1.0"`** (GUI từ chối daemon không compatible); trả `HealthResponse {status, api_version, daemon_version}`; 401 → `MinewrapError::unauthorized`.
- `list_instances()` / `snapshot(id)` — trả raw serde_json (GUI tự map); 404 → `gone`; 401 → `unauthorised`.
- `action(id, action, body)` — generic POST `/api/v1/instances/{id}/{action}` (start/stop/restart/command).
- `backfill_logs(id, limit, since_seq)` — REST backfill (`?limit&since_seq`), dùng khi UI chưa có WS.
- `discord_test(id)` — 1-1 remote test, trả JSON raw.
- `events_ws_url()` / `console_ws_url(id)` — dựng URL ws/wss (thay scheme http→ws) — GUI connect thông qua `events_connect()` (tokio-tungstenite) rồi spawn forward loop theo protocol của `minewrapd`.
- `state_from_error(err)` — map code lỗi → `NodeState` cho UI.

### 5.2 `types.rs` (118 dòng)
`MinewrapError {code, message}` — envelope chuẩn khớp `ARCHITECTURE.md` (codes: `offline / unauthorised / incompatible_version / gone / invalid`) + constructors; `Display` + `std::error::Error`. `NodeSummary {id, name, url, is_local, state}` (UI-Facing **không có token**); `NodeState` enum `Connecting / Connected / Offline / Unauthorised / Incompatible`; `LOCAL_NODE_ID = "local"`.

---

## 6. Logic chi tiết từng module — src-tauri (GUI shell)

> Tổng 1.648 dòng Rust — purpose: **"thin IPC layer"**: không core logic gameplay, token không vào webview, local node nhúng core.

### 6.1 `main.rs` (328 dòng)
1. `config_dir()` — dùng `XDG_CONFIG_HOME` (`$XDG_CONFIG_HOME/minewrap`) hoặc `~/.config/minewrap`; `default_config_path()` — `MINEWRAP_CONFIG` env override → `~/.config/minewrap/minewrap.toml` nếu tồn tại → **migrate legacy** config nằm cạnh binary/AppImage → fallback tạo file từ `DaemonConfig::default()`. (AppImage-safe.)
2. `bundled_daemon_path()` — tìm `minewrapd` cạnh exe (`<dir>/minewrapd`, `binaries/minewrapd[-triple]` — AppImage `usr/bin` contract). **Lưu ý thiết kế:** `ensure_daemon_running()` (sidecar spawn + pre-flight health rồi đăng ký node) tồn tại nhưng `main()` **cố tình không auto-spawn** — desktop muốn GUI-exit = dừng toàn bộ; sidecar path chỉ dành cho packaging headless/remote scenarios.
3. `NodeService::load(config_path)` — fail-soft: nếu file config lỗi dùng defaults + save lại rồi `NodeService::from_config` (không panic).
4. Tauri Builder: plugin `dialog`; `.manage(NodeService)`; `setup` → thread riêng dựng **tokio runtime multi-thread** để chạy `spawn_forwarder_future` (Event forwarder — §2.5). `invoke_handler` đăng ký toàn bộ 22 command. `run` handler: **`ExitRequested`** → `prevent_exit()` rồi spawn thread cleanup: `stop_all_local()` (timeout 8 s — dispatch Stop cho mọi instance local) → `process::exit(0)`; atomic `EXITING` tránh double-cleanup.
5. Forwarder future — gom `LogLine` theo instance (tích lines thành batch, giữ first_seq/last_seq), emit `logs:batch`; `StateChange` → emit `state:changed`. Đảm bảo UI local node và remote node dùng chung Message shape (parity thiết kế).

### 6.2 `lib.rs` (14 dòng)
`pub mod commands / node_service / types`; re-export `NodeService`, `MinewrapError`, `NodeState`; ghi chú thiết kế quid: frontend KHÔNG đụng process/file/socket trực tiếp.

### 6.3 `node_service.rs` (876 dòng)
Trọng tâm thứ hai sau core:

- **`NodeState`** — state machine per-node (Connecting → Connected → Offline / Unauthorised / Incompatible), cùng re-try có thống nhất.
- **`NodeService`** — load config GUI (`DaemonConfig`), cấu trúc: **local node** (nhúng: `Arc<EventBus>` + map `id → Handle` của ProcessManager owner; điều khiển/log buffer trực tiếp) + các **remote node** (`RemoteClient`, key theo id). `is_local` flag cho UI.
- Health check per-node — định kỳ gọi `/health`, chuyển NodeState + phát `nodes:changed`; **disconnect → đưa lỗi → `state_from_error`** mapping.
- Routing mọi operation: `node_id == "local"` → dispatch nhúng; khác → RemoteClient; **cả 2 đường trả cùng DTO shape cho IPC** (khokay UI cần biết khác nhau).
- Control & state: `instance_start/stop/restart` — local: `send_control` (bounded, đầy → trả "busy"); remote: POST route tương đương. `send_command` — local dùng Control::SendCommand; remote POST `/command`.
- Log: local `buffer.tail/since`; remote `backfill_logs` (limit & since_seq).
- Config: `get_config/update_config` — local đi core patch + persist xuống file GUI; remote PUT tương đương.
- Instance CRUD: `add_instance/remove_instance` (local: insert config + spawn manager; remove: stop rồi ghi bỏ; remote: tương đương qua REST).
- Utility: `discord_test`, `list_mods`, `toggle_mod`, `read/write_properties`, `scan_launch`, `detect_java` — local gọi core static fns; remote gọi REST.
- **Event listening**: local subcribe bus wildcard; remote connect `/events` (1 subscriber/node); forward như StateChange/LogLine → cùng 1 forwarder → IPC webview.

### 6.4 `commands.rs` (306 dòng)
22 `#[tauri::command]`, danh sách trùng khớp `generate_handler![]`: `list_nodes, add_node, remove_node, list_instances, get_snapshot, instance_start, instance_stop, instance_restart, send_command, get_logs, get_config, update_config, add_instance, remove_instance, detect_java, scan_launch, read_properties, write_properties, list_mods, toggle_mod, discord_test, health`. Mỗi command: `State<NodeService>` + `node_id: Option<String>` (default local); trả `Result<T, MinewrapError>` — **mọi lỗi đều envelope**, không panic rơi vào webview. Validate input ở mức command (vd. instance-id pattern) để không để lỗ hỏng trực tiếp.

### 6.5 `types.rs` (112 dòng)
Bản mirror `minewrap-remote::types` cho đảm bảo "same envelope": `MinewrapError`, `NodeSummary`, `NodeState` … re-export qua `lib.rs`.

---

## 7. Logic chi tiết frontend Svelte

> Svelte 5 (runes `$state`), TypeScript. Chỉ biblio logic trung tâm bàn về IPC — mục tiêu: "smart thin frontend".

### 7.1 `main.ts` (9 dòng)
Bootstrap: mount `App` vào `#app`; import global `styles/tokens.css`.

### 7.2 `App.svelte` (288 dòng)
- Shell chính: sidebar (tree node/instance — chọn `selectedNode/selectedInstance`) + page area theo `view` (`tree` | `add`).
- Load nodes/instances qua adapter vào state; **selection instance là "console target"**. Mỗi chuyển node/instance, các sub-view re-attach store/subscriptions.
- **Layout view** — các view (`{#if}` conditional mount, chỉ giữ view đang mở): Dashboard cards → Console/Logs/Properties/Mods/Settings tabs; action-error hiển theo `formatError` chuẩn.
- Attach Notification dispatcher (global toast) — nhận từ event bus của UI.

### 7.3 `ipc/*` — lớp trừu tượng backend adapter (quan trọng)
- **`mod.ts` (225 dòng)** — contract interface `IpcAdapter`: `listNodes/addNode/removeNode/listInstances/getSnapshot/instanceStart/Stop/Restart/sendCommand/getLogs/getConfig/updateConfig/addInstance/removeInstance/detectJava/scanLaunch/readProperties/writeProperties/listMods/toggleMod/discordTest/health` + listeners `onLogsBatch / onStateChange / onNodesChanged`. DTO: `LogLine {seq, ts, line}`, `LogBatch {instanceId, lines, firstSeq, lastSeq}` — khớp 1-1 wire Rust.
- **`tauri.ts` (135 dòng)** — impl thật bằng `@tauri-apps/api`: `invoke("<command>", {nodeId, ...})`; `listen("logs:batch" / "state:changed" / "nodes:changed")`, map name kebab-case.
- **`mock.ts` (290 dòng)** — adapter mock offline Full: node fake + 2 instances, log gen theo pha (starting lines → Done → online → stream định kỳ); delay simulate; dùng cho UI dev/tests mà không cần Rust.
- **`factory.ts` (17 dòng)** — chọn adapter: trong Tauri webview → `tauri`; browser dev → `mock`.

### 7.4 `stores/console.ts` (135 dòng)
- Svelte store (writable) giữ **ring 1000 dòng** (`DEFAULT_RING`): state `{lines, firstSeq, lastSeq, stick, total}`.
- **`append(batch)`** — concat + trim về ring; `appendBatch()` — dedupe theo `seq` (v1 ConsoleModel parity), hỗ trợ merge khi re-open; `total` để "jump to latest".
- Auto-scroll "stick to bottom" ngắt khi user kéo lên; chỉ tiếp tục khi user kéo lại đáy.
- `attach(adapter)/detach()` — lifecycle listener (mỗi đổi instance/node attach mới); để đồng bộ `getLogs` (backfill REST) và `onLogsBatch` stream; được dùng bởi Console view.

### 7.5 Components (`ui/src/components/`)
- **`Dashboard.svelte` (187)** — tổng quan instances/node: badges trạng thái (online/unresponsive…), uptime, players/latency/version; nhấn instance → mở detail; refresh qua `state:changed` events.
- **`Console.svelte` (262)** — màn log terminal: list ring 1000 (throttle render), auto-scroll stick, input command (Enter gửi bằng `sendCommand`), đồng bộ tail qua `logs:batch`; **ANSI-to-HTML**: strip untrusted tags, chỉ color-code tin cậy (được review).
- **`Wizard.svelte` (286)** — add instance có hướng dẫn: chọn work dir (dialog `tauri-plugin-dialog`), gọi `scanLaunch` để show detected type/version + list candidates + "suggest launch args" (kế thừa logic `launch.rs`), JavaPicker, JVM flags (kèm preset Aikar), cuối cùng `addInstance`.
- **`AddInstance.svelte` (134)** — form đơn giản (không wizard): work_dir/java/jvm/launch args; validate duplicate-id; dùng chung dialog file; gọi `addInstance`.
- **`JavaPicker.svelte` (162)** — gọi `detectJava` (→ `detect_all()` qua IPC), lọc major ≥ requirement, chọn runtime; hiển thị vendor/version/source; có "custom path" nhập tay.
- **`Settings.svelte` (439)** — editor config: daemon fields (host/port/data_dir/unresponsive…) + từng instance (probe/restart/discord…); hành động thông qua `getConfig → update` (JSON patch chuẩn theo backend `patch_instance`); webhook chỉ hiện `webhook_set` state; toggle Discord events.
- **`Nodes.svelte` (167)** — quản lý node remote: input URL + token → `addNode`; health/state retry display; token không bao giờ hiện tại UI (chỉ placeholder).
- **`Notifications.svelte` (252)** — toast stack cho StateChange/RestartLoop/error + auto-dismiss; tiêu thụ từ App central dispatcher.
- **`Properties.svelte` (182)** — đọc server.properties qua IPC → view theo format round-trip (giữ nguyên cấu trúc file), edit per-cell → `writeProperties` (persist không sort/lốc file); validate key từ ASPET backend.
- **`Mods.svelte` (152)** — list mods (name/size/enabled), search-box client-side, toggle (`toggleMod`), hint cần restart server để áp dụng.
- **`Select.svelte` (125)** — component select generic dùng nhiều nơi (dropdown, picker), hỗ trợ label/filter/error.

### 7.6 `styles/tokens.css` (75) + `lib/formatError.ts` (31)
- `tokens.css` — biến theme (color/spacing/font-contrast).
- `formatError.ts` — biến `MinewrapError`/Error thành chuỗi friendly (code → hiển thị: `offline`/`unauthorised`/… mapping).
- `vite-env.d.ts` (9) — kiểu env Vite.

---

## 8. Hợp đồng API REST + WebSocket

### 8.1 REST routes (`minewrapd` — API v1.0; số bản parity cho IPC local)

| Method | Route | Auth | Ý nghĩa |
|---|---|---|---|
| GET | `/health` | public | `{status, api_version:"1.0", daemon_version:"1.9.3"}` |
| GET | `/openapi.json` | token | descriptor tự sinh |
| GET | `/api/v1/instances` | token | danh sách summary (combined_state/players/version/latency) |
| GET | `/api/v1/instances/{id}` | token | snapshot đầy đủ (process + probe merged) |
| POST | `/api/v1/instances/{id}/start` | token | start server (state machine) |
| POST | `/api/v1/instances/{id}/stop` | token | dừng (TERM→KILL escalation) |
| POST | `/api/v1/instances/{id}/restart` | token | composite stop+start |
| POST | `/api/v1/instances/{id}/command` | token | `{"command":"…"}` → stdin |
| GET | `/api/v1/instances/{id}/logs` | token | `?limit&since_seq` — tail/since backfill |
| GET/PUT | `/api/v1/instances/{id}/config` | token | đọc / patch config (persist TOML) |
| POST | `/api/v1/instances/{id}/discord/test` | token | gửi embed test qua webhook đã cấu hình |
| GET/PUT | `/api/v1/instances/{id}/properties` | token | server.properties round-trip |
| GET | `/api/v1/instances/{id}/mods` | token | list `.jar` & `.jar.disabled` |
| POST | `/api/v1/instances/{id}/mods/toggle` | token | `{"name":"…"}` — rename enable/disable |
| GET (WS) | `/console/{id}` | Bearer tại handshake | stream log + command |
| GET (WS) | `/events` | Bearer tại handshake | wildcard all-events stream |

REST error shape: `{detail: string}` với status tương ứng 401/404/409/422.

### 8.2 WS message shapes

- **`/console/{id}`**:
  - server → client (đầu tiên): `{"type":"log","instance_id":"…","lines":[LogLine…]}` (backfill) rồi `{"type":"snapshot","snapshot":…}`; sau đó `{"type":"log",…}` live (batched).
  - client → server: `{"type":"command","command":"say hi"}` → server confirm `{"type":"command_result","accepted":true}`.
- **`/events`**: mỗi event một JSON `{"kind":"state_change"|"restart_loop"|"log_line", …}` serialization của enum `Event`.

### 8.3 IPC events (Tauri → webview)

| Event | Payload | phát từ |
|---|---|---|
| `logs:batch` | `{instanceId, lines, firstSeq, lastSeq}` | forwarder (local forwarder & remote forwarder cùng shape) |
| `state:changed` | `{instanceId, oldState, newState, reason}` | forwarder |
| `nodes:changed` | `{nodeId, state}` | NodeService health loop |

---

## 9. Cấu hình `minewrap.toml` — schema & giá trị mặc định

```toml
[daemon]
host = "127.0.0.1"                 # bind address (loopback-only → SSH forward để remote)
port = 8080                        # REST + WS
data_dir = "./data"                # táng token (0600), discord state file…
status_poll_interval = 15.0        # giây — interval được UI dùng khi poll snapshot
unresponsive_after_failures = 2    # probe fail liên tiếp trước khi "unresponsive"

[daemon.defaults]                  # áp cho instance không override
startup_timeout = 300.0            # chưa "Done" sau_ms → crashed (reason startup_timeout)
stop_timeout = 60.0                # chờ exit sau TERM
kill_grace_seconds = 5.0           # TERM → KILL grace
done_regex = 'Done \(\d+(\.\d+)?s\)! For help'  # regex đánh dấu online (custom được)
log_buffer_lines = 500             # ring in-memory per instance
log_max_bytes = 10_485_760         # 10 MiB trước rotate
log_backups = 3                    # log.1 … log.3

[[instances]]
id = "survival"                    # unique-slug (map key + bus topic)
name = "Survival"
work_dir = "/srv/mc/survival"
java_path = "/usr/lib/jvm/…/bin/java"
jvm_args    = ["-Xms2G", "-Xmx4G"]
launch_args = ["-jar", "server.jar", "nogui"]
autostart = false

[instances.probe]                  # SLP
host = "127.0.0.1"
port = 25565
timeout = 3.0

[instances.restart]
policy = "on-crash"                # hoặc "never"
max_retries = 5
backoff_base_seconds = 5.0
backoff_max_seconds = 300.0
reset_after = 600.0

[instances.discord]
webhook_url = ""                   # secret (Serialize chỉ xuất webhook_set)
enabled_events = ["start", "stop", "crash", "restart_loop"]
max_log_chars = 1500               # tối đa trong embed (≤ 4096)
```

Token: `data_dir/token` (0600, hex 64 ký tự) hoặc env `MINEWRAP_TOKEN`; sinh đầu tiên in stdout **một lần duy nhất**.

---

## 10. Đóng gói & vận hành

- **AppImage** (`packaging/build-linux.sh`): build Rust + `pnpm build` frontend; bundle `usr/bin/{minewrap-tauri, minewrapd}` + `AppRun` (entry `usr/bin/minewrap-tauri`, đảm bảo writable XDG dir; daemon phải tiện cạnh `usr/bin` hoặc `binaries/` — `bundled_daemon_path()` hỗ trợ cả hai).
- **systemd**: `packaging/minewrapd.service` — headless node; `MINEWRAP_CONFIG` env; harden với ProtectSystem/ProtectHome cho phạm vi writable chỉ `data_dir`.
- **Tauri**: `src-tauri/tauri.conf.json` — frontendDist `../ui/dist`, binary `minewrap-tauri`, window config.

---

## 11. Trạng thái build/test hiện tại

Kết quả tái triển ngay trước khi viết báo cáo (output trực tiếp trên máy này):

| Câu lệnh | Kết quả |
|---|---|
| `cargo test --workspace --release` | **47 tests PASS** (minewrap-core: 45 unit + minewrapd auth: 2) |
| `cargo build --release --workspace` | OK — `target/release/{minewrapd, minewrap-tauri}` |
| `pnpm run check` (svelte-check) | **0 errors, 0 warnings** |

---

## 12. Phương pháp đo bộ nhớ

### 12.1 Câu hỏi cần trả lời

> RAM mà **bản thân wrapper** chiếm giữ — khi **không mở server nào**, với **1 instance cấu hình nhưng không start**, với **3 instances offline**, và với **1 instance đang chạy**. **KHÔNG tính** RAM JVM server. Cộng thêm 2 kịch bản ứng xử: **có client WS console live**, và **GUI desktop**.

### 12.2 Công cụ & quy trình (đo lần cuối, 2026-11-11)

- **Sampler** (`/tmp/opencode/memtest/memsample.py`): duyệt **cây tiến trình** theo bố-mãi (`/proc/<pid>/status:PPid`) từ pid daemon, **1 giây/lần**; mỗi tiến trình cộng dồn từ **`/proc/<pid>/smaps_rollup`** (không duyệt từng mapping nên không lag không skip): RSS, PSS, USS (Private_Clean + Private_Dirty), Swap; cùng `/proc/<pid>/status` cho Threads / VmHWM / VmPeak.
- **Kịch bản runner** (`/tmp/opencode/memtest/scenario.py`) — spawn daemon release binary với `MINEWRAP_CONFIG=<scenario>.toml` (port riêng 8081–8084, `data_dir` riêng), đợi `/health` = 200, một số scenario POST `/instances/survival/start`, rồi **chạy sampler N giây**; cuối `pkill fakejava` + `SIGKILL` daemon; token đọc `data_dir/token`.
- **Kịch bản WS** — thêm client `wsclient.py` (Python socket thuần — HTTP Upgrade handshake với header Bearer; giữ kết nối open, trả pong khi ping) trỏ vào `/console/<id>` như một client thật — đo chi phí khi có consumer stream.
- **Kịch bản ENV** — `scenario_env.py` cho phép nạp env-file để thử biến runtime (sử dụng cho bài thí nghiệm `TOKIO_WORKER_THREADS=2`).
- **Quy tắc loại trừ stub server**: các config kịch bản dùng `java_path = <stub>` trỏ vào một **bash script** (`fakejava`) giả lập Minecraft: in **burst 2000 dòng** log lúc start, rồi in `"Done (1.234s)! For help"`; sau đó stream dòng "session" mỗi 0.5 s. Sampler **loại trừ mọi cây con của stub** (bash/zip con của subshell/`sleep`): loại theo **token cmdline** cho node gốc và **cắt toàn bộ subtree** của node bị loại — lưu ý khó: tiến trình con như `sleep` có cmdline không chứa marker (số liệu đầu của kịch bản "run" có sai lệch VmPeak = 368 MiB và procs = 2 do đếm nhầm các tiến trình con của stub; quy tắc subtree đã khắc phục).
- **Thời gian lấy mẫu**: 25–45 giây/kịch bản. Điều kiện ổn định: min ≈ median ≈ max trong suốt phép đo (jitter run-to-run ≤ 0.1–0.15 MiB trên RSS).
- **Output CSV** lưu `/tmp/opencode/memtest/csv_<label>.csv` (t, rss, pss, uss, swap, threads, procs, vmpeak, hwm) để phân tích.

### 12.3 Môi trường đo

| Thông số | Giá trị |
|---|---|
| OS | Fedora Linux 44 Workstation |
| Kernel | 7.2.15-200.fc44.x86_64 |
| CPU | 12 lõi (`nproc = 12`) |
| RAM hệ thống | 15 GiB (kịch bản chạy song song không đụng nhau) |
| Build | release profile workspace: `lto = true, codegen-units = 1, strip = true` |
| Binaries | minewrapd 5.59 MiB, minewrap-tauri 10.39 MiB (không symbol) |
| Runtime Tokio | mặc định: `worker_threads = nproc = 12` (không cấu hình riêng) |
| GUI | Wayland (session hiện có) — WebKitGTK 4.1 và GTK3 libs (ldd verified) |

### 12.4 Định nghĩa chỉ số

- **RSS** — tổng RAM resident: gồm cả *shared library pages* (libc, GTK, TLS…); vì cùng library có thể được map bởi tiến trình khác, RSS **overestimate "owned"**.
- **PSS** — chia shared pages theo số tiến trình cùng giữ; **số gần "thực dùng" nhất**, chuẩn hơn RSS khi so sánh.
- **USS** — chỉ phần riêng (Private Dirty + Private Clean); là **floor** "chi phí trực tiếp mà chỉ có thể vì tiến trình này".
- **VmPeak / VmHWM** — virtual peak (liberal reserve của address spaces: thread stack reserve, mmap region — **KHÔNG phải RAM**) và RSS high-watermark.

---

## 13. Kết quả đo bộ nhớ thực tế

### 13.1 minewrapd — bảng tổng hợp (median; [min–max]; MiB; sampler tree loại trừ stub)

| Kịch bản | procs | threads | RSS | PSS | USS | VmPeak (tree) | VmHWM |
|---|---|---|---|---|---|---|---|
| **S0**: daemon + **0 instance** | 1 | 13 | **5.56** [5.56–5.56] *(run 2: 5.67)* | **3.30** *(run 2: 3.37)* | **3.27** *(run 2: 3.34)* | 145.40 / 141.39 | 5.56–5.67 |
| **S1**: daemon + **1 instance (offline)** | 1 | 13 | **6.31** | **4.04** | **4.01** | 141.39 | 6.31 |
| **S3**: daemon + **3 instances (offline)** | 1 | 13 | **6.48** | **4.24** | **4.21** | 141.39 | 6.48 |
| **SR**: S1 + **instance đang chạy** (stub: burst 2000 dòng + stream 0.5 s) | 1 | 13 | **6.51** | **4.19** | **4.16** | 143.39 | 6.51 |
| **SW**: SR + **1 client WS console** (backfill + stream) | 1 | 13 | **7.43** | **5.06** | **5.03** | 141.39 | 7.43 |
| **SW2**: S0 nhưng **`TOKIO_WORKER_THREADS=2`** (thí nghiệm hỗ trợ đề nghị D1) | 1 | **3** | **5.43** | **3.23** | **3.21** | 141.39 | 5.43 |

Tính chất dữ liệu: min ≈ max trong cùng kịch bản (biến thiên < 0.05 MiB), run-to-run jitter ≤ 0.15 MiB → đo ổn định, đủ đáng tin để làm baseline.

### 13.2 minewrap-tauri (GUI) — đo tree (3 tiến trình; idle Dashboard; 1 instance offline; không mở console)

| Thành phần | RSS | PSS | Private_Dirty (≈ USS) | threads |
|---|---|---|---|---|
| `minewrap-tauri` (Rust shell: GTK + webkit + NodeService nhúng) | **178.10** | **74.26** | **43.52** | 38 |
| `WebKitNetworkProcess` | 56.82 | 21.71 | 11.39 | 11 |
| `WebKitWebProcess` (JS engine + DOM) | 202.05 | **100.28** | 42.66 | 42 |
| **Tổng cây** | **436.32** [436.18–436.97] | **195.60** | 97.57 | 87 |

- Trạng thái: không bật server; đo 30 giây (jitter ±0.4 MiB); VmHWM tổng 441.69 MiB; **VmPeak tổng ≈ 385 GiB (ảo)** — address space reservations, không phải RAM.

### 13.3 Nhận định dữ liệu

1. **Footprint daemon nhỏ và phẳng:** RSS 5.5 → 7.4 MiB, kể cả có 1 server đang stream log + 1 WS client. PSS (số "honest") chỉ 3.2 → 5.1 MiB — footprint chủ yếu từ runtime tokio/axum + heap cấu hình.
2. **Chi phí per-instance (offline) nhỏ:** Δ(S0→S1) = **+0.75 MiB RSS** — LogBuffer 500 dòng (~25–45 KiB) chỉ chiếm một phần nhỏ; phần còn lại là owner task (stack + Notify + control channel + state + FD của RotatingFile + IPC extension). Δ(S1→S3) = **+0.17 MiB** cho 2 instance thêm (~0.085 MiB/instance — nhiều phần shared).
3. **Chi phí khi đang chạy (stub):** Δ(S1→SR) ≈ **+0.20 MiB** — pipeline xử lý dòng + file write + burst 2000 dòng (ring 500 chỉ giữ 500 dòng cuối) vẫn giữ RSS gần như phẳng — log pipeline hữu hiệu và ổn định về memory.
4. **Chi phí WS client (live console):** Δ(SR→SW) = **+0.92 MiB** — bộ đệm serialization WS + subscription channel 256 + buffering batch 100 dòng/40 ms.
5. **Gốc phần lớn của GUI là WebKit:** tổng 436.3 MiB RSS và PSS 195.6 MiB; riêng các WebKit process chiếm **PSS ≈ 122.0 MiB** (network 21.7 + web 100.3) so với shell Rust chỉ 74.3. USS tổng ~142.6 MiB: shell 43.5 + WebKit ~54.0.
6. **Worker threads tokio = nproc:** daemon chạy **13 threads** (12 workers + 1 main) trên máy 12 lõi — tăng theo số lõi máy (máy 32 lõi sẽ khởi tạo 33 threads). Thí điểm cap 2 workers: **threads 13 → 3**, RSS 5.56 → **5.43 MiB** (−0.13), PSS −0.07; `VmPeak` không đổi (141.4) — xác nhận dự trù đa phần không do thread-stack.
7. Muốn so sánh *kịch bản daemon 0-instance so với run+WS*: basis tối thiểu của wrapper đó là ~3.2 MiB PSS / 5.6 MiB RSS, cao nhất 5.1 MiB PSS / 7.4 MiB RSS khi có console client live.

---

## 14. Phân tích phân bổ bộ nhớ trong tiến trình

Ước lượng vùng nhớ theo cấu trúc code + số đo thực:

**Trong minewrapd (baseline PSS ~3.2–5.1 MiB):**

| Vùng | Ước lượng | Ghi chú |
|---|---|---|
| Text/.rodata của ELF (strip) | ~0.7–1.0 MiB resident | binary 5.6 MiB nhưng không mọi page đều được touch |
| **Runtime tokio (12 workers) + axum/tower** | ~0.5–0.8 MiB | scheduler parking/queues; mỗi worker stack commit ~4–32 KiB theo sử dụng |
| Heap cấu hình (serde/toml parse ở boot) | ~0.3–0.6 MiB | `DaemonConfig::load_from` + instance map |
| **Per-instance**: LogBuffer ring 500 LogLine (seq + ts + String) | ~25–45 KiB | tail 500 dòng × ~50–90 B thực tế/ngoài; phần lớn Δ(S0→S1) = +0.75 MiB là từ phần owner task, phần heap area arena + state + FD file |
| EventBus: mpsc 256 slot/subscriber | ~40–64 KiB per subscriber | LogLine event có String clone → theo ~150–250 B/slot |
| WS client console | ~0.4–0.9 MiB | tungstenite buffer + backfill-200 serialize + batch pool |
| reqwest/rustls (Discord test) | ~hundreds KiB (lazy) | mỗi call tạo `reqwest::Client::new()` — connector pool + TLS ctx ngắn hạn |
| RotatingFile buffers & FD | ~8 KiB/instance | std file buffered write |

**Trong minewrap-tauri (GUI):** phần ăn khớp với cơ chế — WebKit multi-process (JS heap + DOM + graphics buffers + JIT pages), GTK/cairo, và Rust shell (NodeService nhúng core + forwarder + reqwest/rustls + tao/wry infra). Shell PSS 74.3 MiB — GTK/WebKit libs phần lớn là shared, private allocations chủ yếu ở runtime tokio/axum + heap riêng. Chi tiết per-process ở §13.2.

---

## 15. Phương án tối ưu memory footprint

> Chỉ tập trung **giảm/nhất quán bộ nhớ**. Mỗi mục nêu rõ: động cơ (số đo), cách thực hiện, quy mô kỳ vọng (ước lượng từ số đo trong §13), và cách nghiệm thu bằng bộ sampler. Sắp theo **độ đắt-rẻ / độ lợi** — item có bằng chứng đo trực tiếp xếp trước.

### 15.1 minewrapd (daemon)

**[D1] Cập `worker_threads` của runtime Tokio (đo trực tiếp; gain nhỏ RSS nhưng ổn định trên máy đa lõi)**
- Đo: default `worker_threads = nproc` → 13 threads trên máy này; thí nghiệm `TOKIO_WORKER_THREADS=2` → **threads 13 → 3, RSS 5.56 → 5.43 MiB (−0.13), PSS 3.30 → 3.23**.
- Cách: bỏ default nproc — dùng `#[tokio::main(worker_threads = N)]` hoặc đọc từ config (`[daemon] worker_threads`, fallback `2–4` cho workload I/O-bound). Cách khác **không cần sửa code**: set `TOKIO_WORKER_THREADS=2` trong systemd unit (deploy-level).
- Nghiệm thu: chạy lại S0/SR với sampler — kiểm cột `threads` và RSS/PSS; kỳ vọng threads 3–5 & VmPeak không đổi.

**[D2] Lazy-allocate per-instance runtime (LogBuffer + owner task) cho instance offline**
- Đo/liên hệ: Δ(S0→S1) = +0.75 MiB cho 1 instance **chưa từng chạy** — trong đó ring 500 dòng chỉ ~25–45 KiB; phần còn lại là owner task trong status "always-on manager" (instances.rs `start_all()`).
- Cách: chỉ tạo LogBuffer/owner-task khi instance **được start lần đầu** hoặc nhận log đầu tiên; giữ per-instance static config trong map (Option<Arc<…>>).
- Kỳ vọng: daemon boot với N instance offline sẽ gần S0 (thay vì +0.75 + 0.085×(N−1) MiB); hiệu quả tăng khi N lớn.
- Nghiệm thu: đo S1 với config 10 instance offline trước/sau; kỳ vọng RSS plateau gần S0 + O(1).

**[D3] Ring LogBuffer dùng allocation-chunk ổn định (giảm fragment churn khi burst)**
- Cơ chế hiện tại: `VecDeque<LogLine>` giữ `String` → mỗi push/pop phát allocation; burst 2000 dòng (SR) tạo/evict ~1.500 dòng/s trong vài giây — allocator giữ pages → RSS nhích nhẹ nhưng stable; với nhiều instance burst cùng lúc, fragment tăng.
- Cách: prealloc byte-ring (một `Box<[u8]>` circular + mảng offset/seq ở header) hoặc tái sử dụng buffer String theo slot (reuse-on-evict) — API `tail/since` giữ nguyên.
- Kỳ vọng: giảm churn & fragmentation, RSS peak ổn hơn qua các đợt burst (không bị "lệch" giữa các instance).
- Nghiệm thu: đo SR với `FAKE_BURST=5000` trước/sau (sampler không đổi; chạy đồng thời nhiều instance để cộng fragment).

**[D4] Giảm slot EventBus bounded 256 → 32/64 per subscriber**
- Cơ chế: mỗi Subscription cấp channel 256 slot; LogLine event có String clone. Với wildcard subscriber (GUI `/events`, mỗi console WS...) tổng slot = 256 × subscribers.
- Cách: giảm cap (vẫn giữ v1 semantics "slow-consumer drop + seq-gap"); hoặc config daemon điều chỉnh.
- Kỳ vọng: RAM per subscriber drop gióng theo tỷ lệ cap (256 → 64: −~75% pool per sub; sub đơn ≈ 30–50 KiB tiết kiệm).
- Nghiệm thu: đo SW nhiều client (3–4 WS) trước/sau.

**[D5] Dùng chung một `reqwest::Client` cho Discord test & Notifier (mỗi call hiện tạo `Client::new()`)**
- Cơ chế: `/discord/test` tạo `reqwest::Client::new()` mỗi lần gọi — TLS context/connector pool/hyper infra allocations tồn tại phạm vi call; sau drop, allocator không luôn trả OS ngay → RSS noise.
- Cách: một `OnceLock<reqwest::Client>` toàn daemon (và trong GUI cho NodeService remote clients), reuse keep-alive.
- Kỳ vọng: ổn giữ RSS khi gọi nhiều lần; giảm allocation edge case.
- Nghiệm thu: gọi lặp `/discord/test` × 20 (webhook fake) đo RSS trước/sau.

**[D6] `[profile.release] panic = "abort"` (giảm nhỏ binary/runtime unwinding tables)**
- Chỉ làm khi chấp nhận mất unwinding (hợp cho daemon không cần catch-unwind); làm binary nhỏ lại vài %, text pages resident giảm chút. Effort rất thấp; ưu tiên thấp vì gain nhỏ.

**Không nên làm (theo bằng chứng đo):**
- **Đổi allocator (jemalloc/mimalloc)** — RSS phẳng (min = max), footprint chỉ vài MiB, thêm phụ thuộc C cho gain không đo được; từ chối.
- **Refactor axum → hyper thuần** — gain binary/text nhỏ (< 0.3 MiB) so với công sức và tăng surface bug; từ chối cho mục tiêu memory.
- **`MALLOC_ARENA_MAX`** — không đo được arena bloat trên footprint này; chỉ giữ như **best-practice deploy** (systemd env `MALLOC_ARENA_MAX=2`), không sửa code.

### 15.2 GUI (minewrap-tauri + webview)

Đo: toàn cây RSS 436.3 MiB / PSS 195.6 MiB; **các WebKit process chiếm phần lớn footprint** — nên tối ưu ở hai phạm vi: (1) phần có thể thay đổi trong phạm vi project (Rust shell, JS/DOM), (2) env fallback cho WebKit.

**[G1] Giới hạn & lifecycle ring console phía JS (thiết kế hiện tại: 1000 dòng/instance; store chỉ detach listener, KHÔNG thu hồi contents khi view unmount)**
- Đo: `WebKitWebProcess` PSS = 100.3 MiB. Store giữ `lines` 1000 entry trong webview; Console view có thể render phần lớn của chúng trong DOM.
- Cách: (a) giảm `DEFAULT_RING` 1000 → 300 (có tùy chọn "Full history" truy vấn REST `logs?limit=` riêng khi cần tra cứu); (b) khi Console/Dashboard unmount — **detach + reset store** (`set(initial)`) để GC lấy lại; (c) giữ số DOM node render đồng thời nhỏ (chunk/inner-window render, chỉ giữ ~200 DOM node).
- Kỳ vọng: giảm JS heap + DOM tree của webview (theo trăm KiB→ vài MiB tuỳ log density); ổn định PSS webview khi stream dài.
- Nghiệm thu: đo GUI tree 60 giây stream console với FAKE_STREAM_EVERY=0.05 (log dày) trước/sau — so PSS WebKitWebProcess.

**[G2] Env fallback cho WebKit trên máy không GPU/VM (`WEBKIT_DISABLE_COMPOSITING_MODE=1`, `WEBKIT_DISABLE_DMABUF_RENDERER=1`)**
- Lý do: compositor/renderer buffers & textures chiếm phần lớn "graphics pages" trong WebKit; trên máy không GPU, stack đồ hoạ rơi về software rendering — resident của webprocess giảm theo cấp độ thiết bị.
- Cách: AppRun/tài liệu đưa env opt-in; hoặc auto-detect (không có GL) fallback.
- Kỳ vọng: trên VM/host không GPU, RSS/PSS WebKit giảm đáng kể, mất chi phí compositor.
- Nghiệm thu: đo trên máy VM không GPU có/không env; so PSS tree.

**[G3] Giới hạn workers của forwarder runtime trong GUI shell**
- Cơ chế: `main.rs` spawn thread riêng dựng **tokio multi-thread** (default nproc = 12 workers) chỉ để chạy forwarder event — quy mô nhỏ so với năng lực runtime mặc định.
- Cách: `Builder::new_multi_thread().worker_threads(1–2)` cho forwarder runtime; command handlers vẫn dùng Tauri async runtime.
- Kỳ vọng: threads GUI shell giảm (~10 threads), nhận scheduler/stack commit ít hơn; theo đo D1 tương tự daemon.
- Nghiệm thu: đo `threads` của minewrap-tauri process trước/sau.

**[G4] Reuse reqwest clients trong NodeService (per-node pool thay vì mỗi call một client) + WS reconnect không tạo client mới mỗi lần**
- Tương tự D5 phía GUI; giảm allocations per-call và tận dụng keep-alive.
- Nghiệm thu: đo nhiều lần remote-node calls (máy cục bộ + node fake) và so RSS drop curve.

**[G5] Giữ 1 WebKitWebProcess/1 NetworkProcess (hiện trạng đã tối đa)** — đo cho thấy chỉ có 1 web + 1 network process; giữ khi thêm feature: tránh mỗi panel/window sinh web process riêng (multi-window Tauri default sinh webview riêng — cần chốt strategy nếu thêm cửa sổ).

### 15.3 Bảng ưu tiên (sau khi cân bằng risk/benefit)

| # | Mục | Đối tượng | Kỳ vọng (đo phía §13) | Effort |
|---|---|---|---|---|
| G1 | ring JS 1000→300 + detach/reset + DOM cap | GUI webview | PSS webview giảm khi stream dài/switch view | thấp |
| G3 | tokio workers forwarder 12→1–2 | GUI shell | −~10 threads; RSS shell giảm nhẹ | rất thấp |
| D1 | tokio workers daemon 12→2–4 | minewrapd | threads 13→3–5; RSS −0.1–0.3 MiB; ổn hơn máy nhiều lõi | rất thấp |
| G2 | WebKit compositor env fallback | GUI (VM host không GPU) | RSS/PSS WebKit giảm theo người dùng máy | thấp |
| D2 | lazy per-instance runtime | minewrapd | bỏ +0.75 MiB đầu mỗi instance offline; N lớn lợi rõ | trung |
| D5 | shared reqwest Client (daemon/GUI) | daemon + GUI | giảm per-call allocations & RSS noise | thấp |
| D4 | EventBus cap 256→64 | minewrapd | −~75% pool per subscriber | thấp |
| D3 | ring allocator chunked | minewrapd | chống fragment khi burst nhiều instance | trung |
| D6 | panic=abort | minewrapd (và GUI) | binary/text nhỏ vài % | rất thấp |

### 15.4 Quy trình nghiệm thu

Dùng lại chính bộ đo của báo cáo (`/tmp/opencode/memtest/`): `memsample.py` + `scenario.py`/`scenario_env.py` + config kịch bản (`idle0/idle1/idle3/run` + `wsclient.py` + env-file). Tiêu chuẩn pass cho mỗi tối ưu:

1. Chạy lại đủ 6 kịch bản S0 / S1 / S3 / SR / SW / GUI trên cùng máy, đối chiếu **min / median threads / RSS / PSS / USS** so baseline của báo cáo này — ngưỡng: S0 ±0.2 MiB; S1 ±0.2; S3 ±0.3; SW ±1.0 MiB RSS; GUI ±10 MiB PSS / ±30 MiB RSS.
2. Kỳ vọng số threads daemon target 3–5 (tùy cap chọn 2–4) và GUI shell tương ứng.
3. Không được regression về chức năng: tất cả 47 tests Rust + svelte-check phải vẫn pass sau mỗi tối ưu.

---

### Phân tích phụ: lưu ý đo (nếu team muốn tái hiện)

- Dùng **process-tree từ `/proc`** để tổng đúng các tiến trình thuộc đúng cây (chuẩn hơn `ps` — không nhầm process cùng tên ở nơi khác).
- Loại trừ stub **theo subtree** — không theo cmdline từng pid riêng lẻ (vì con của stub như `sleep` không chứa marker); sai số VmPeak = 368 MiB và procs = 2 ở lần đo thăm dò đầu đã khắc phục nhờ quy tắc này.
- PSS là chỉ số "đối thẳng" khi so với tiến trình khác trên cùng máy; USS là floor cho chi phí riêng; RSS dùng cho báo cáo tổng quan tải hệ thống.
- `VmPeak` 141.4 MiB của daemon **không là RAM**: gồm reservations address-space (thread-stack reserve, mmap region, địa chỉ shared libs) — chỉ dùng như tín hiệu phòng lệch (guard-rail) khi debug, không cộng vào công bố RAM thật.

---

*Báo cáo soạn tại `/home/kimhoanglong/dev-MC-server-Wrapper` — Minewrap v1.9.3, ngày 2026-11-11. Toàn bộ số đo lặp được bằng bộ script trong `/tmp/opencode/memtest/` (phương pháp chi tiết §12–§15).*
