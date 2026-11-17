# Journal — phiên GLM sandbox 2 (2026-11-17, tiếp tục phiên 1)

## Bối cảnh

Người dùng gửi lại credential gateway sau khi restart service trên máy họ (PID
266562) kèm hướng dẫn điều phối đã "kiểm chứng thật" từ phía agent OpenCode
của họ. Kỳ vọng: kết nối được và bắt đầu điều phối A1–A5 trên máy thật
(thư mục SPNC), tải 2 PDF bị chặn bằng mạng nhà người dùng.

## Việc đã làm

1. **Test kết nối với credential mới: VẪN 401.** Điều tra hệ thống:
   - Tunnel sống (200 ở /doc); request TỚI ĐƯỢC server thật — bằng chứng
     quyết định: route pairing công khai `/auth/connect/xyz` trả đúng thông
     báo riêng của OpenCode "Pairing link expired or already used" (khác
     thông báo auth). Middleware xử lý sec-fetch-mode đúng như mã nguồn v2.3.0
     (không header → có www-authenticate; sec-fetch-mode: cors → không).
   - Cả 3 dạng auth đều bị server từ chối: Basic header, ?auth_token= (nằm
     trong URL, không liên quan header), python urllib (stack khác).
   - Base64 do chính người dùng cung cấp giải mã ra đúng chuỗi tôi dùng —
     loại sai lệch copy.
   - Kết luận D9: mật khẩu trong tin nhắn là mật khẩu CŨ (đã bị đổi sau khi
     họ copy — hoặc service get password trả giá trị khác với giá trị runtime).
     Theo kỷ luật: DỪNG, không thử nữa.
2. **upload/ trống** — người dùng chưa gửi bản nháp cũ / PDF.
3. **Săn ICAS Chiang bằng 11 đường mới** (Korpal PhD AMU qua 3 biến thể URL —
   tất cả dính Cloudflare Turnstile; academia.edu 403; MDPI 403; IASJ timeout
   90s; KU ScholarWorks timeout; scholar.archive.org rate-limit; CORE redirect
   vòng; archive.org wayback connection refused; Warwick + UChicago tải được
   nhưng không liên quan ICAS; ERIC mở được nhưng không nhắc Chiang). Kết luận
   D10: giữ [CHƯA XÁC MINH], đã ghi đủ bằng chứng từng đường.
   - Manh mối còn hứa hẹn cho phiên sau: Korpal thesis PDF (AMU) — Turnstile
     chỉ chặn bot, trình duyệt thật của người dùng mở được; IASJ bài 2011
     (iasj.rdd.edu.iq) dùng cả FLCAS lẫn ICAS của Chiang.
4. **A4 Bài 1 HOÀN TẤT**: So_tay_hoc_tap_Bai_1.docx (+pdf) — 6 trang, postcheck
   0 lỗi, nội dung dạy "đọc và đánh giá tài liệu nghiên cứu" dùng 100% ví dụ
   thật từ A1 (Ferdowsi [insert location], IJRISS review 3 ngày, Wang đổi
   chiều thang, 2 nguồn bot-block). Ghi chú verify: "insert location" trong
   bài là trích dẫn có chủ đích (mô tả lỗi biên tập) — đã cho phép trong
   verify_bai1.py theo ngữ cảnh.

## Bài học phiên này

- 401 hai phiên liên tiếp với 2 mật khẩu khác nhau do người dùng cung cấp →
  khả năng cao service get password trả mật khẩu khác mật khẩu runtime, hoặc
  có tầng auth khác. Lần sau: yêu cầu người dùng CHÍNH HỌ curl từ máy họ đến
  tunnel bằng mật khẩu đó; nếu máy họ 200 mà sandbox 401 → vấn đề là IP/geo
  của tunnel chặn; nếu máy họ cũng 401 → mật khẩu sai ngay từ nguồn.
- Cloudflare Turnstile là bức tường phổ biến nhất chặn thesis PDF (AMU, KU);
  với sandbox không có trình duyệt thật thì bó tay — đưa URL cho người dùng.
- Cách verify docx mới: cho phép token "xấu" trong NGỮ CẢNH trích dẫn có chủ
  đích (verify_bai1.py) — không loại máy móc.

## Trạng thái cuối phiên

- Deliverables: Bài 0 + Bài 1 (docx+pdf) trong download/ + mirror archive.
- Ledgers: GLOSSARY +6 mục Bài 1; DECISION_LOG +D9/D10/D11;
  SO_TAY_HOC_TAP Bài 1 hoàn tất.
- OPEN_QUESTIONS: U3 (mật khẩu gateway) vẫn mở; U1 (bản nháp cũ) vẫn mở;
  thêm việc nhờ người dùng: tải Korpal thesis PDF (Turnstile chặn bot) +
  IASJ 2011 PDF (server chậm) — 2 ứng viên trích ICAS.
