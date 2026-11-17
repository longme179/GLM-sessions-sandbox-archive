# Journal — phiên GLM sandbox 4 (2026-11-17, tiếp nối phiên 3)

## Bối cảnh mở phiên

Người dùng chạy `opencode pair` lần 3 (sau 2 lần đầu: 1 lần link hết hạn vì trễ
chuyển phiên, 1 lần client phía người dùng tự tiêu thụ link). Output pair lần 3
in ra credential — khớp 100% mật khẩu đã lưu. Tunnel subdomain không đổi.

## Xác minh gateway — BẬC NHẢY CHẨN ĐOÁN: 401 BIẾN MẤT

- `/api/info` từ sandbox: **200** — pid 266562, v2.3.0, hostname fedora. Cùng
  PID với phiên 3 → server KHÔNG restart giữa hai phiên.
- Ổn định 5/5 lần (12:22–12:36 UTC), kể cả ép qua edge IPv4 cũ 168.220.93.252
  bằng `curl --resolve`.
- Egress sandbox là IP datacenter Alibaba HK (AS45102, xoay vòng 3 IP) — nghĩa là
  giả thuyết D12 "tunnel bóc auth với IP datacenter" **bị bác bỏ trực tiếp**:
  nếu đó là chính sách thì sandbox phải 401 như phiên 1–3.
- ps trên host: server start 16:31:56 +07 (09:01 UTC), uptime 7h59 — phủ trọn
  cả cửa sổ lỗi 10:02–11:28 UTC. Lỗi không nằm ở server.

## Chẩn đoán cuối (D14)

401 phiên 1–3 là **lỗi tạm thời trên chuỗi tunnel** (fly.io edge hoặc daemon
client): header Authorization bị tháo trong forwarding trong cửa sổ ~1,5 giờ,
tự hồi phục. Không phải chính sách IP, không phải mật khẩu, không phải MITM,
không phải stack HTTP. Toàn bộ bằng chứng + phương pháp bác bỏ từng giả thuyết
lưu `research/opencode-auth-401-analysis.md` (phụ lục phiên 4).

Thí nghiệm 2 thí nghiệm phân biệt còn lại từ phiên 3:
1. **opencode pair** (3 lần): link 1 lần, client phía người dùng tiêu thụ ngay
   khi pair → tôi curl chỉ còn "expired or already used". Credential in ra chính
   là mật khẩu gốc (mã nguồn auth_230.ts: token pair = HMAC ký bằng mật khẩu).
   → pair KHÔNG sinh credential mới; không cần cho mục tiêu truy cập.
2. **4G hotspot**: không cần chạy nữa — kiểm chứng dương (sandbox datacenter
   200) đã thay thế phép phân biệt.

## Đồng bộ hạ tầng

- **fs/write (endpoint experimental) KHÔNG ghi filesystem host**: trả 200 kèm
  path đúng nhưng file không xuất hiện trên host (ghi vào sandbox filesystem
  nội bộ của opencode server). Đồng bộ thật phải qua `/api/shell` + base64 —
  15/15 file ghi thật, md5 khớp bản local. Bài học vận hành quan trọng nhất
  phiên này về hạ tầng opencode v2.3.0.
- SPNC trên host giờ có cấu trúc phẳng: LEDGERS/ (7 sổ, D14 đã lên), agents/ (6),
  journal/ (phiên 4), research/ (phân tích 401). Lỗi ban đầu: script sync cộng
  đôi prefix đường dẫn (SPNC/projects/SPNC/...) — đã dọn phẳng + rm thư mục lồng.
- Host KHÔNG tải được Chiang/Dong PDF (hdl.handle.net + repositories.lib.utexas.edu
  đều 403 từ cả host lẫn sandbox — UTexas chặn bot/VPN) → vẫn cần người dùng tải
  bằng trình duyệt thật (việc U-trên sổ).
- Session chat ses_e172f6ec... không sạch (90k input tokens) — sub-agent vẫn cần
  session mới khi chạy trên host.

## Sản xuất phiên 4

- **Báo cáo tiếng Việt** (docx+pdf): chẩn đoán cuối 401 + 2 thí nghiệm + A3
  deliverable — cho người dùng nắm toàn cảnh sự cố hạ tầng và cách ứng phó.
- Sổ: D14 (hiệu chỉnh D12), U3 giải quyết, phụ lục research phiên 4.

## Bài học phiên này

- **Kiểm chứng dương (positive control) là bắt buộc trước khi chốt chẩn đoán
  "theo nguồn IP"**: phiên 3 đã loại trừ gần hết (MITM, mật khẩu, stack) nhưng
  thiếu phép dương "IP datacenter + auth đúng → có 200 không?" — nếu làm từ
  phiên 3, đã thấy ngay chính sách-chặn-IP không đứng vững vì chưa từng có
  control dương cho thấy IP nhà luôn 200 NGAY CÙNG thời điểm sandbox 401.
- opencode pair không sinh credential mới — token HMAC ký bằng mật khẩu gốc;
  rotate mật khẩu tự thu hồi mọi token pair (SESSION_TTL 30 ngày).
- Egress sandbox xoay vòng nhiều IP cùng ASN — khi test IP-based, ghi chú IP
  từng request (ipify mỗi lần), không giả định IP cố định.
- opencode v2.3.0 có 2 lớp filesystem: `/api/experimental/fs/write` ghi trong
  sandbox nội bộ (200 nhưng không thấy trên host); `/api/shell` chạy host thật.
  Muốn ghi file cho người dùng: base64 qua shell. Muốn đọc: đọc qua shell rồi
  base64 về (oc_fetch.py).
- Khi đồng bộ nhiều file qua API: kiểm chứng NGAY bằng ls + md5 từ phía nhận,
  không tin vào HTTP 200 (fs/write đã trả 200 mà file không tới đích).

## Trạng thái cuối phiên

- Gateway: 200 ổn định; sổ SPNC đã sync lên host /home/kimhoanglong/Documents/SPNC.
- Chờ người dùng: U1 (bản nháp cũ), U2 (thông tin học phần), U4 (ưu tiên sản
  phẩm), PDF Chiang/Dong tải bằng trình duyệt thật.
- Đề xuất khi rảnh: rotate mật khẩu (đã lộ trong transcript nhiều lần) —
  `opencode service set password "$NEW"`; mọi token pair tự hết hiệu lực theo.
