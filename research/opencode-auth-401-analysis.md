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

---

# PHỤ LỤC PHIÊN 4 (2026-11-17, 12:22–12:36 UTC) — D12 BỊ BÁC BỎ, CHẨN ĐOÁN CUỐI

## Thí nghiệm 1 — opencode pair (3 lần chạy trên máy người dùng)

| Lần | Code | Kết quả khi tôi curl /auth/connect/<code> | Diễn giải |
|---|---|---|---|
| 1 | 77mSJEmEnPU8alHI-oo0WA | 401 "Pairing link expired or already used" | Hết 5 phút (trễ do chuyển phiên hết context) |
| 2 | uRbd6kxMTGUEhp6UzHGdvg | (không curl kịp) — output in credential | Client pair phía người dùng đã tiêu thụ link |
| 3 | DhHcN0AyMN2PWcPWjWMIcg | 401 "Pairing link expired or already used" | Idem — link 1 lần, client tiêu thụ ngay |

Kết luận: luồng pair hoạt động đúng thiết kế; credential trong output pair CHÍNH LÀ
mật khẩu service hiện hành (không sinh token mới) — mã nguồn auth_230.ts: token
pair = HMAC ký bằng chính mật khẩu, nên "USER/PASSWORD" in ra là mật khẩu gốc.
Thí nghiệm pair KHÔNG còn cần thiết cho mục tiêu truy cập (Basic auth đã thông).

## Thí nghiệm 2 — 4G hotspot (KHÔNG cần chạy nữa)

Mục đích cũ là phân biệt "tunnel chặn IP datacenter" vs "lỗi khác". Kiểm chứng dương
từ sandbox (IP Alibaba HK = datacenter) auth 200 ổn định đã thay thế: nếu tunnel
chặn datacenter thì sandbox phải 401 như phiên 1–3. → Đóng thí nghiệm này.

## Bằng chứng bác bỏ D12 (thu thập phiên 4)

1. **Máy chủ không đổi**: /api/info → pid 266562, hostname fedora, v2.3.0 — trùng
   PID phiên 3; ps trên host: start Tue Nov 17 16:31:56 2026 (+07), uptime 7h59,
   KHÔNG restart giữa 2 phiên.
2. **Mật khẩu không đổi**: credential từ `opencode pair` phiên 4 = chuỗi đã lưu.
3. **Cùng edge fly.io**: DNS A = 168.220.93.252 (fly.io anycast, AS40509); ép
   `curl --resolve` qua đúng IP edge cũ đó + Basic auth → 200. Nghĩa là cùng đường
   wire phiên 3, giờ thông.
4. **Nguồn là IP datacenter**: egress sandbox xoay vòng 47.57.232.232 /
   8.212.10.159 / 47.57.242.119 — cả 3 đều Alibaba (US) Technology, AS45102, HK.
   ipinfo xác nhận AS45102; đây là IP datacenter đúng nghĩa.
5. **Ổn định lặp lại**: 5/5 curl /api/info 200 liên tiếp (12:22–12:36 UTC), không
   có 401 nào xen kẽ; message endpoint (nặng hơn) cũng 200.

## Chẩn đoán cuối

401 phiên 1–3 (cửa sổ ~10:02–11:28 UTC) là **lỗi tạm thời trên chuỗi tunnel**
(fly.io edge hoặc daemon tunnel client phía người dùng): header Authorization bị
tháo/bỏ trong forwarding trong khoảng thời gian đó, sau đó tự hồi phục. Không phải
chính sách chặn IP datacenter (D12 sai), không phải mật khẩu (đúng), không phải
MITM (cert thật), không phải stack HTTP (3 stack đều bị như nhau).

Cơ chế cụ thể bên trong edge/daemon không xác minh được từ ngoài (hộp đen) — đây
là giới hạn của điều tra từ sandbox; nếu tái diễn cần bắt gói tin trên host
(tcpdump port 49374 trong lúc lỗi) để chốt tầng nào tháo header.

## Việc cần làm nếu 401 tái diễn

1. Thử lại sau 5–15 phút trước khi kết luận (lỗi tạm thời đã gặp 1 lần).
2. Nếu kéo dài: user chạy tcpdump trên host (tcpdump -i any port 49374 -w dump.pcap)
   trong khi sandbox curl → xem header Authorization có tới server không.
3. Không đổi mật khẩu khi đang 401 (mật khẩu chưa bao giờ sai) — chờ xác minh.
