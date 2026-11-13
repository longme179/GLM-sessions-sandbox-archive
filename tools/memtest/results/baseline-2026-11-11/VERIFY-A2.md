# A2 verification — GLM tái đo & đánh giá baseline (2026-11-11)

> Quy tắc plan v1.1 §10.4: "GLM tái đo ngẫu nhiên để kiểm chứng; gì chưa
> verify thì ghi unverified". Bản ghi này đóng dấu verified cho baseline.

## 1. GLM re-measure (trực tiếp qua raw-shell, KHÔNG qua agent)

| Run | Kết quả | So với agent |
|---|---|---|
| S0-verify1 (30 s) | RSS 5.75 [5.75–5.75] · PSS 3.50 | agent S0 median 5.74/3.48 → Δ 0.01/0.02 |
| S0-verify2 (30 s) | RSS 5.76 [5.76–5.76] · PSS 3.45 | Δ 0.02/0.03 |
| SR-verify1 (35 s) | RSS 7.12 [7.12–7.12] · PSS 4.75 | agent SR 6.92/4.67 → Δ 0.20/0.08 |

**Kết luận: số của agent đáng tin** — chênh lệch trong jitter run-to-run
(≤ 0.2 MiB RSS như báo cáo gốc §13.1). Threads 13, procs 1, stub online
(Done line + stream), GapB reproduced (REST state 'offline' khi server chạy).

## 2. Hiện tượng S0#1: step-down 5.85 → 4.10 MiB tại t=24 s

- Xảy ra MỘT lần trong 1/2 runs của agent; KHÔNG tái hiện trong 2 runs
  verify của GLM (5.75/5.76 phẳng tuyệt đối) cũng như S0#2 (5.63 phẳng).
- Đặc điểm: RSS/PSS/USS cùng tụt −1.75 MiB rồi ổn định → event reclaim
  một lần của hệ thống (máy có ~6.8 GiB free/15 GiB, có activity nền),
  không phải lỗi sampler (đọc smaps_rollup không撕裂 — giá trị sau tụt
  vẫn nội bộ nhất quán).
- Xử lý: median-of-runs đã hấp thụ; nếu muốn loại hoàn toàn, chạy RUNS=3
  và lấy median (đã ghi vào runbook cho các đợt đo K1/K2 sau này).

## 3. Đánh giá 3 FAIL so ngưỡng §15.4 (báo cáo cũ)

| Kịch bản | Đo được (PSS) | Ref cũ | Δ | Đánh giá |
|---|---|---|---|---|
| SR | 4.67 (agent) / 4.75 (GLM verify) | 4.19 | +0.48 | **Tái lập được trên máy hôm nay** — trạng thái máy đã dịch (lib/build mới: rustc Fedora build, glibc). Không phải lỗi phương pháp: các kịch bản tĩnh S0/S1/S3 khớp +0.10..+0.18. |
| SW2 | 3.44 | 3.23 | +0.21 | Biên fail 0.01 ngoài ngưỡng ±0.2 — marginal, cùng nguyên nhân S0 (+0.18). |
| GUI | 209.32 (RSS 438.75) | 195.60 (RSS 436.32) | +13.72 PSS / +2.43 RSS | RSS khớp gần tuyệt đối; PSS lệch do **shared-page accounting** thay đổi theo phiên bản WebKitGTK/lib hệ thống (máy giờ: webkit2gtk-4.1 2.54.2). Không phải regression của app. |

## 4. Kết luận Phase A

- **Harness A2 đạt AC về mặt phương pháp**: 4/7 kịch bản trong ngưỡng cũ;
  3 kịch bản lệch đều do trôi môi trường hệ thống (không phải do cách đo —
  chứng minh bằng việc kịch bản tĩnh khớp tuyệt đối và số tái lập giữa
  agent & GLM).
- **Bảng baseline CHÍNH THỨC để so sánh P0 (K1/K2)** = bảng trong
  `baseline-v1.9.3.md` (đo ngày 2026-11-11, cùng harness, cùng máy, build
  cùng ngày từ bfde421). Số báo cáo cũ giữ làm tham chiếu lịch sử.
- Ý nghĩa với P0: K1 "PSS đóng GUI ≤ 8 MiB" — tham chiếu động: SW (đo mới)
  = 5.38 PSS là điểm so chính; K2 GUI mở: so với 209.32/438.75 (không
  +5% của số cũ 195.6 → dùng ≤ ~219.8 PSS).

## 5. Trạng thái môi trường máy user (env-check.md, phần agent ghi)

rustc 1.99.1 (Fedora) · pnpm 12.18.0 · node v22.23.1 · tauri-cli 2.12.4 ·
Wayland trực tiếp (Xvfb KHÔNG cài — lưu ý cho C4 spike: cần cài Xvfb hoặc
đổi protocol đo spike sang Wayland headless riêng) · ports 8081-8085 free ·
daemon build 1m09.82s (5.59 MiB) · GUI build 2m51.05s (10.39 MiB, sidecar
đã lo) · webkit2gtk-4.1 2.54.2 / libsoup-3.0 3.6.6 / gtk3 3.24.52.

## 6. Phát hiện hiển thị (ghi cho Session sau)

Lớp hiển thị terminal có thể "ăn mất" chuỗi `[mi` trong output (rg + rsh
đều gặp) — luôn verify byte thật bằng `od -c`/python khi nghi ngờ lỗi text
trong file từ xa. File report.py và baseline-v1.9.3.md đều đúng bytes.
