# Phân tích 401 gateway OpenCode (phiên 3, 2026-11-17)

## Chuỗi kết nối (đã xác minh)
sandbox → (Internet) → fly.io edge 168.220.93.252 (cert ZeroSSL *.x3v7ggvsseh7.opentunnel.xyz)
→ tunnel client daemon (máy người dùng, Fedora) → localhost:49374 opencode server v2.3.0

## Bằng chứng đã thu thập
1. Mật khẩu ĐÚNG: người dùng curl từ máy họ qua tunnel → 200 (pid 266562 khớp /api/info).
2. Sandbox: 12+ biến thể auth (Basic header/Bearer/x-auth-token/cookie/auth_token query
   raw+b64+urlencoded, UA trình duyệt, sec-fetch-mode cors, node fetch, python urllib,
   http1.1) → tất cả 401 "Authentication required" CÓ www-authenticate (sinh bởi
   middleware auth thật của server, authorization.ts).
3. WebFetch (mạng khác sandbox) → 401.
4. KHÔNG MITM: cert tunnel ZeroSSL thật, chuỗi sạch; kết nối trực tiếp không proxy;
   httpbin.org đối chứng header sống sót qua egress sandbox.
5. Query string ĐẠT server: /api/pty/fakepty123/connect?ticket=abc bỏ qua auth (đúng
   logic authorization.ts:88-91) và trả 400 "Expected a string starting with pty"
   — lỗi validation của HANDLER THẬT. Vậy query tới server nguyên vẹn.
6. Path đạt server nguyên vẹn: /auth/connect/dGVzdA trả "Pairing link expired" (handler thật).
7. Password brute-force 8 biến thể tự nhiên (case, ký tự nhìn giống l/I/1, _) → 401 hết.

## Mâu thuẫn chưa giải thích được
Query tới server nguyên vẹn (bằng chứng 5) nhưng auth_token=b64 đúng format vẫn 401.
Nếu server nhận được auth_token đúng, credentialFromRequest decode ra đúng username:password
→ phải 200. Vậy có một tầng (fly edge hoặc tunnel client) biến đổi request theo nguồn IP:
- Hoặc bóc header Authorization + bóc cả query auth_token (nhưng giữ query ticket) — khả thi
  nếu tunnel client whitelist tên query param (chỉ forward ticket/cursor/...).
- Hoặc tunnel client thay header Authorization bằng giá trị khác khi nguồn không phải IP nhà.

## Kết luận thực dụng
Từ sandbox KHÔNG thể qua được auth qua tunnel này (3 stacks HTTP, 2 mạng, 12 biến thể).
Người dùng đã xác nhận 200 từ máy họ → mọi thao tác qua tunnel phải do NGƯỜI DÙNG hoặc
agent OpenCode trên máy họ thực hiện, KHÔNG phải sandbox.

## Hướng đi (xếp theo ưu tiên)
1. NGƯỜI DÙNG test từ mạng khác (4G hotspot): nếu 200 → tunnel chặn theo IP datacenter
   → dùng pairing session token qua cookie từ trình duyệt người dùng (verifySession chấp
   nhận token ở slot password, cookie opencode_session_<port>).
2. `opencode pair` + curl /auth/connect/<code> Accept: application/json → {"token": ...}
   (session token 30 ngày). Gửi token qua tin nhắn → tôi dùng "opencode:<token>" Basic.
   Nếu vẫn 401 (edge bóc header) → token qua cookie opencode_session_443 (tuy yêu cầu
   Origin cùng host — curl gửi được Origin cùng host).
3. Hỏi opencode GitHub/Discord về hành vi auth của tunnel opentunnel.xyz.
