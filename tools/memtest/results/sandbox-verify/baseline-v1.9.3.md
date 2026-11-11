# Baseline v1.9.3 — tái đo bằng harness memtest

- Ngày đo: 2026-11-11T06:38:22
- Máy đo: `Linux 5.10.134-013.15.kangaroo.al8.x86_64 x86_64 GNU/Linux` (ncores = 2)
- Phương pháp: report v1.9.3 §12.2 — sampler cây process 1 Hz, `smaps_rollup` (RSS/PSS/USS/Swap), loại subtree stub theo cmdline marker `fakejava`; median [min–max] mỗi kịch bản.
- Ngưỡng so khớp §15.4: S0/S1/SW2 ±0,2 · S3/SR ±0,3 · SW ±1,0 · GUI ±10 PSS / ±30 RSS (MiB). PASS = |Δ median PSS| (GUI: cả RSS) trong ngưỡng.

| Kịch bản | runs | RSS | PSS | USS | threads | procs | PSS ref | ΔPSS | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **S0** — daemon + 0 instance | 1 | 5.49 [5.49–5.49] | 3.58 [3.58–3.58] | 3.35 | 3 | 1 | 3.30 | +0.28 | **FAIL** |
| **S1** — daemon + 1 instance (offline) | 1 | 6.25 [6.25–6.25] | 4.43 [4.43–4.43] | 4.21 | 3 | 1 | 4.04 | +0.39 | **FAIL** |
| **S3** — daemon + 3 instances (offline) | 1 | 7.08 [7.08–7.08] | 5.18 [5.18–5.18] | 4.94 | 3 | 1 | 4.24 | +0.94 | **FAIL** |
| **SR** — S1 + instance đang chạy (stub burst 2000 + stream 0,5 s) | 1 | 6.99 [6.99–6.99] | 4.99 [4.99–4.99] | 4.77 | 3 | 1 | 4.19 | +0.80 | **FAIL** |
| **SW** — SR + 1 client WS console (backfill + stream) | 1 | 7.47 [7.47–7.47] | 5.57 [5.56–5.57] | 5.36 | 3 | 1 | 5.06 | +0.51 | **PASS** |
| **SW2** — S0 nhưng TOKIO_WORKER_THREADS=2 (thí nghiệm D1) | 1 | 5.73 [5.73–5.73] | 3.76 [3.76–3.76] | 3.52 | 3 | 1 | 3.23 | +0.53 | **FAIL** |
| **GUI** — cây minewrap-tauri (3 tiến trình, idle Dashboard) | 1 | 8.52 [8.52–8.52] | 1.31 [1.31–1.31] | 0.57 | 4 | 4 | 195.60 | -194.29 | **FAIL** |

**Tổng: 1 PASS / 7 đo được.**

Ghi chú: số đo sandbox (Debian, 2 lõi) chỉ để xác minh cơ chế harness — baseline chính thức phải đo trên máy user (Fedora 44, 12 lõi) theo plan v1.1 task A2. GUI scenario cần display (Wayland session hoặc Xvfb).
