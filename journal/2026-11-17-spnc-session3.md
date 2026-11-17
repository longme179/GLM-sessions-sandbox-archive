# Journal — phiên GLM sandbox 3 (2026-11-17, tiếp nối phiên 2)

## Bối cảnh

Người dùng trả lời yêu cầu tự kiểm tra: chạy `opencode service get password` (ra
đúng chuỗi mật khẩu đã gửi) và curl từ máy họ qua tunnel → **200**, pid 266562
khớp. Nghĩa là mật khẩu ĐÚNG và server chấp nhận nó — vấn đề nằm ở phía sandbox.

## Điều tra 401 — chốt được bản chất (D12)

Kết luận sau khi loại trừ lần lượt:

1. **Không phải MITM**: cert tunnel ZeroSSL thật của *.x3v7ggvsseh7.opentunnel.xyz,
   httpbin đối chứng Let's Encrypt thật; kết nối trực tiếp 168.220.93.252
   (fly.io edge, anycast), không proxy trong egress sandbox.
2. **Không phải sai mật khẩu**: brute-force 8 biến thể tự nhiên (case, l/I/1,
   g twice, padding) đều 401; chuỗi base64 người dùng cung cấp decode khớp 100%.
3. **Không phải stack HTTP**: curl, node fetch, python urllib, WebFetch (mạng
   khác sandbox) — tất cả 401.
4. **Query string ĐẠT server nguyên vẹn** (bằng chứng vàng): `/api/pty/x/connect?ticket=abc`
   bỏ qua auth (đúng logic authorization.ts:88-91) và trả 400 từ handler thật
   ("Expected a string starting with pty"). Vậy request của tôi tới server với
   query nguyên vẹn — nhưng `?auth_token=` (đúng format base64 của web client)
   vẫn bị 401 "Authentication required" CÓ www-authenticate (sinh từ middleware
   auth thật).
5. Giải thích khớp mọi bằng chứng: **tunnel (fly edge hoặc daemon tunnel client
   trên máy người dùng) biến đổi request theo nguồn IP** — với IP nhà người
   dùng: nguyên vẹn (200); với IP datacenter (sandbox + WebFetch): bóc
   Authorization header VÀ bóc query auth_token (nhưng giữ nguyên ticket, path).
   Có thể là biện pháp chống lạm dụng của opentunnel.xyz với datacenter IP.

Đã đọc toàn bộ mã nguồn auth v2.3.0 (packages/server/src/middleware/authorization.ts,
auth.ts, handlers/server.ts, pairing.ts, cli pair handler) — clone sparse từ
GitHub. Cơ chế: Basic header | ?auth_token= (base64) | session cookie pairing
(token HMAC 30 ngày, dùng được ở slot password). Toàn bộ phân tích lưu
`research/opencode-auth-401-analysis.md`.

## Việc tiếp theo cho người dùng (2 thí nghiệm phân biệt cuối)

1. Test từ mạng khác (4G hotspot): `curl -s -u "opencode:$PW" $URL/api/info`
   → nếu 200: tunnel chặn IP datacenter, giải pháp = pair token qua tin nhắn.
2. `opencode pair` → lấy link /auth/connect/<code> → curl với Accept: application/json
   → {"token": ...} → gửi token (30 ngày hiệu lực).

## Sản xuất phiên 3 (D13)

- **A3 Chương 3 Methodology bản nháp** — 7 trang, mục 3.1–3.8 (thiết kế mixed-
  methods giải thích, participants + bảng 3.1, công cụ 3 phần + bảng 3.2, kiểm
  định 5 bước + không EFA, thu thập, phân tích Braun & Clarke + bảng 3.3, đạo
  đức, vị thế nhà nghiên cứu). Placeholder CAM đánh dấu chờ U1/U2/U5 — đúng luật
  D5 (không bịa số liệu). Verify code PASS (thứ tự, bảng, placeholder, nội dung
  then chốt từ ledgers); postcheck 0 lỗi.
- Model phiên này không đọc được ảnh → visual check thay bằng text-layout check
  pdftotext (bảng 3 cột đủ, không dòng trống) + cùng khuôn layout đã kiểm ảnh
  ở Bài 0/1.

## Bài học phiên này

- Bằng chứng vàng để phân biệt "request tới server" vs "edge chặn": route công
  khai có hành vi khác biệt theo query (PTY ticket) — kế thừa kỹ thuật fingerprint
  middleware từ phiên 2.
- `opencode pair` + Accept: application/json → JSON {token} thay vì redirect —
  đọc từ handlers/server.ts:36-47. Session token dùng được ở slot password
  (auth.ts:33-37) — nếu người dùng gửi token, thử ngay cả khi mật khẩu thường
  vẫn 401.
- Sandbox không bao giờ tự giải được bài tunnel-theo-IP; cần người dùng chạy
  từ mạng khác để chốt.

## Trạng thái cuối phiên

- Deliverables mới: Chuong3_Methodology_nhap.docx (+pdf) — download/ + archive.
- Ledgers: DECISION_LOG +D12/D13. Research: opencode-auth-401-analysis.md.
- Chờ người dùng: U1 (bản nháp cũ), U2 (thông tin học phần), thí nghiệm 4G,
  pair token, 3 PDF (Chiang, Korpal, Dong).
