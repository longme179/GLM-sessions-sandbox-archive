# memtest — Minewrap memory measurement harness (STANDALONE)

> **Chính sách Q8 (user khóa ngày 2026-11-11):** bộ tool này KHÔNG bao giờ
> được commit vào repo GitHub `Minewrap`. Repo app chỉ chứa tài liệu + code
> app + build script. Working copy sống trên máy user tại `~/dev-memtest/`,
> bản gốc (master) nằm trong archive repo GLM tại `tools/memtest/`.

Tái tạo đúng phương pháp đo của báo cáo kiến trúc v1.9.3 §12.2 để mọi số
đo so sánh trực tiếp được với baseline (S0…SW, GUI) và dùng lại cho P0
(đo K1/K2) + spike toolkit (protocol C4).

## Cấu trúc

| File | Vai trò |
|---|---|
| `memsample.py` | Sampler cây process 1 Hz theo `PPid`; đọc `smaps_rollup` (RSS/PSS/USS/Swap) + `status` (Threads/VmPeak/VmHWM); **loại subtree stub** theo cmdline marker; xuất CSV + JSON median [min–max] |
| `scenario.py` | Runner 1 kịch bản daemon: spawn minewrapd release với `MINEWRAP_CONFIG`, đợi `/health`, (tuỳ chọn) start instance + gắn 1 WS client, chạy sampler, dọn dẹp |
| `scenario_env.py` | Như scenario.py nhưng nạp env-file trước (thí nghiệm `TOKIO_WORKER_THREADS=2` → SW2) |
| `gui_scenario.py` | Đo cây GUI `minewrap-tauri` (3 tiến trình, idle Dashboard); hỗ trợ `--xvfb :99` cho headless |
| `wsclient.py` | WS console client socket thuần: handshake Bearer, trả pong, đếm message |
| `fakejava` | Stub "Minecraft server": burst 2000 dòng → dòng `Done (1.234s)! For help` (khớp `done_regex`) → stream 0,5 s/dòng; đọc-và-bỏ stdin |
| `configs/*.toml` | S0/S1/S3/SR/GUI — port 8081–8085, `data_dir` riêng; `env-wt2.env` cho SW2 |
| `run_baseline.sh` | Chạy đủ kịch bản A2 + sinh `results/baseline-v1.9.3.md` |
| `report.py` | Gộp `results/*.json` → bảng median [min–max] + đối chiếu ngưỡng §15.4 |
| `results/` | CSV (`csv_<label>.csv`), JSON tổng hợp, log daemon/GUI, báo cáo |

## Sử dụng

```bash
# 1 kịch bản đơn lẻ
python3 scenario.py --config configs/run.toml \
    --binary /path/to/minewrapd --label SR --seconds 35 --start survival

# toàn bộ baseline (A2) — daemon + GUI
./run_baseline.sh /path/to/minewrapd /path/to/minewrap-tauri

# SW2 (cap worker threads) + GUI headless
RUNS=2 SW2=1 GUI_DISPLAY=xvfb DISPLAY_VAL=:99 \
    ./run_baseline.sh /path/to/minewrapd /path/to/minewrap-tauri
```

Yêu cầu: `python3 ≥ 3.11` (tomllib), Linux có `/proc/<pid>/smaps_rollup`
(kernel ≥ 4.14). Không cần thư viện ngoài.

## Kịch bản & số tham chiếu (báo cáo v1.9.3 §13)

| Label | Ý nghĩa | RSS / PSS ref (MiB) | Ngưỡng §15.4 |
|---|---|---|---|
| S0 | daemon + 0 instance | 5.56 / 3.30 | ±0.2 |
| S1 | + 1 instance offline | 6.31 / 4.04 | ±0.2 |
| S3 | + 3 instances offline | 6.48 / 4.24 | ±0.3 |
| SR | + instance đang chạy (stub) | 6.51 / 4.19 | ±0.3 |
| SW | + 1 WS console client | 7.43 / 5.06 | ±1.0 |
| SW2 | S0 + `TOKIO_WORKER_THREADS=2` | 5.43 / 3.23 (3 threads) | ±0.2 |
| GUI | cây minewrap-tauri idle | 436.32 / 195.60 | ±10 PSS / ±30 RSS |

## Quy tắc đo (không được đổi khi so sánh với baseline)

1. Sampler duyệt **cây process từ pid daemon/GUI** theo `PPid` — chuẩn hơn
   `ps` (không nhầm tiến trình cùng tên).
2. Đọc `smaps_rollup` (không duyệt từng mapping) 1 Hz: RSS, PSS,
   USS = Private_Clean + Private_Dirty, Swap; `status`: Threads/VmPeak/VmHWM.
3. **Loại subtree stub**: mọi node (khác root) có cmdline chứa marker
   `fakejava` → cắt cả subtree (con `sleep`/subshell không chứa marker nhưng
   bị cắt theo cha). Bài học từ lần đo đầu: đếm nhầm con stub làm VmPeak
   vọt +368 MiB.
4. Mỗi kịch bản đo 25–45 s; ổn định = min ≈ median ≈ max; jitter run-to-run
   ≤ 0.1–0.15 MiB. Báo cáo median [min–max] của ≥2 runs.
5. Config mỗi kịch bản dùng port + `data_dir` riêng; data_dir được xoá sạch
   đầu mỗi run (token sinh mới, không mang state cũ).
6. `VmPeak` là address-space reserve (thread stack, mmap) — KHÔNG phải RAM;
   chỉ dùng làm guard-rail debug, không công bố thành RAM.

## Triển khai lên máy user (protocol agent)

1. Agent tạo `~/dev-memtest/` (nếu chưa có).
2. Chuyển từng file byte-exact: `printf %s <base64> | base64 -d > path`,
   đối chiếu `wc -c` + sha256 với `MANIFEST`.
3. `chmod +x fakejava run_baseline.sh`.
4. Build minewrapd + minewrap-tauri release từ repo (build máy user),
   rồi `./run_baseline.sh <minewrapd> [minewrap-tauri]`.
5. Kết quả: `results/baseline-v1.9.3.md` + CSV — gửi về GLM review
   (fetch ngược qua `oc_fetch.py`), bản sao commit vào archive repo.

## KPI dùng lại sau này

- **K1 (P0)**: PSS toàn wrapper khi đóng GUI ≤ 8 MiB — đo bằng chính harness
  này (kịch bản: daemon + 1 server thật chạy + 1 WS client + Discord svc).
- **C4 (spike)**: `memsample.py` trên cây app spike dưới `Xvfb :99`,
  3 kịch bản × 3 runs, median [min–max].
