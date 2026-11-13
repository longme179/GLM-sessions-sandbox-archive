# Baseline v1.9.3 — tái đo bằng harness memtest

- Ngày đo: 2026-11-11T14:06:45
- Máy đo: `Linux 7.2.15-200.fc44.x86_64 x86_64 GNU/Linux` (ncores = 12)
- Phương pháp: report v1.9.3 §12.2 — sampler cây process 1 Hz, `smaps_rollup` (RSS/PSS/USS/Swap), loại subtree stub theo cmdline marker `fakejava`; median [min–max] mỗi kịch bản.
- Ngưỡng so khớp §15.4: S0/S1/SW2 ±0,2 · S3/SR ±0,3 · SW ±1,0 · GUI ±10 PSS / ±30 RSS (MiB). PASS = |Δ median PSS| (GUI: cả RSS) trong ngưỡng.

| Kịch bản | runs | RSS | PSS | USS | threads | procs | PSS ref | ΔPSS | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **S0** — daemon + 0 instance | 2 | 5.74 [4.10–5.85] | 3.48 [1.85–3.60] | 3.45 | 13 | 1 | 3.30 | +0.18 | **PASS** |
| **S1** — daemon + 1 instance (offline) | 2 | 6.40 [6.33–6.46] | 4.14 [4.08–4.20] | 4.11 | 13 | 1 | 4.04 | +0.10 | **PASS** |
| **S3** — daemon + 3 instances (offline) | 2 | 6.63 [6.59–6.67] | 4.40 [4.33–4.48] | 4.37 | 13 | 1 | 4.24 | +0.16 | **PASS** |
| **SR** — S1 + instance đang chạy (stub burst 2000 + stream 0,5 s) | 2 | 6.92 [6.88–6.96] | 4.67 [4.62–4.72] | 4.64 | 13 | 1 | 4.19 | +0.48 | **FAIL** |
| **SW** — SR + 1 client WS console (backfill + stream) | 2 | 7.59 [7.52–7.67] | 5.38 [5.27–5.49] | 5.35 | 13 | 1 | 5.06 | +0.32 | **PASS** |
| **SW2** — S0 nhưng TOKIO_WORKER_THREADS=2 (thí nghiệm D1) | 2 | 5.75 [5.67–5.83] | 3.44 [3.41–3.47] | 3.41 | 3 | 1 | 3.23 | +0.21 | **FAIL** |
| **GUI** — cây minewrap-tauri (3 tiến trình, idle Dashboard) | 2 | 438.75 [438.21–439.66] | 209.32 [208.28–210.04] | 142.46 | 87 | 3 | 195.60 | +13.72 | **FAIL** |

**Tổng: 4 PASS / 7 đo được.**

Ghi chú: số đo sandbox (Debian, 2 lõi) chỉ để xác minh cơ chế harness — baseline chính thức phải đo trên máy user (Fedora 44, 12 lõi) theo plan v1.1 task A2. GUI scenario cần display (Wayland session hoặc Xvfb).
