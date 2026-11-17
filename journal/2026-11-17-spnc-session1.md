# Journal — phiên GLM sandbox

## 2026-11-17 — Session 1: SPNC bootstrap (orchestrator + 5 agent)

**Nhiệm vụ**: đóng vai orchestrator điều phối 5 sub-agent cho khóa luận lo âu
phiên dịch đuổi (HCMUE), song song dạy lại cho người dùng (mới về phương pháp
nghiên cứu).

**Việc đã làm:**
1. Kiểm tra sandbox: `upload/` trống (không có bản nháp cũ — U1 vẫn mở),
   `/home/kimhoanglong/Documents/SPNC` KHÔNG tồn tại trong sandbox (đó là
   đường dẫn máy desktop của người dùng, chỉ tới được qua gateway OpenCode).
2. Gateway OpenCode: 401 với mọi dạng xác thực đúng chuẩn (Basic /
   auth_token / cookie-flow). Đọc mã nguồn OpenCode v2.3.0 trên GitHub
   (anomalyco/opencode — repo sst/opencode đã đổi chủ, 301): username luôn là
   "opencode"; test `sec-fetch-mode` chứng minh request TỚI ĐƯỢC middleware
   → mật khẩu đã bị đổi/rotated. DỪNG theo kỷ luật (không đoán tiếp), đã
   liệt kê U3 xin mật khẩu mới.
3. Clone archive repo (PAT hoạt động OK, user longme179). Dựng
   `projects/SPNC/`: README, LEDGERS (SOURCE_REGISTRY, DECISION_LOG,
   OPEN_QUESTIONS, ITEM_BANK, GLOSSARY), agents/AGENTS-OVERVIEW.md,
   tools/oc_client.py (client cho API v2.3.0 — legacy oc.py/qw.py nhắm API cũ).
4. Khởi chạy A1 (sub-agent nội bộ, Explore/general-purpose) xác minh nguồn;
   A4 viết Bài 0 Sổ tay học tập (docx tiếng Việt) — xem status log README.
   A2/A3/A5 tạm dừng đúng kế hoạch (chờ U1/U2/U4).

**Bài học cho phiên sau (SPNC):**
- Mật khẩu gateway do người dùng cấp MỖI session trong tin bootstrap; nếu 401
  → hỏi ngay ở câu trả lời đầu, đừng tốn 20 bước dò như hôm nay (dù nhờ vậy
  mà vẽ được bản đồ auth v2.3.0 vào oc_client.py).
- Repo sst/opencode → anomalyco/opencode (301); tag v2.3.0 tồn tại; mã auth
  đọc được tại packages/server/src/{auth.ts,middleware/authorization.ts}.
- Người dùng KHÔNG đính kèm bản nháp cũ trong tin đầu → luôn hỏi lại trước
  khi tái tạo item (luật seed).

**Trạng thái các ledger cuối phiên:** SOURCE_REGISTRY (seed nạp, chờ A1 bổ
sung), DECISION_LOG (D1–D8), OPEN_QUESTIONS (U1–U4, G1–G8), ITEM_BANK (chờ
bản nháp), GLOSSARY (6 mục Bài 0), SO_TAY_HOC_TAP (Bài 0 xong, Bài 1–5 kế
hoạch), agents/ đủ 5 hồ sơ + AGENTS-OVERVIEW.

**Bài học kỹ thuật docx (mới, quan trọng cho mọi bài sau):**
1. docx-js 9.15 TỰ sinh mục TOC đầu (hyperlink + PAGEREF + w:dirty) →
   add_toc_placeholders.py của skill chèn thêm → mục đầu LẶP. Với docx-js 9.x:
   KHÔNG chạy script đó; thay bằng postfix tự viết (outlineLvl vào styles.xml,
   updateFields vào settings.xml, footer instrText ROMAN/arabic, xóa
   pgNumType rỗng) — xem scripts/postfix_bai0.py (mirror trong repo này:
   projects/SPNC/tools/).
2. Bìa R5: section bìa PHẢI margin 0 — nếu để margin thường, wrapper 16838 bị
   co, tiêu đề wrap xấu ("LUẬN" rơi dòng riêng).
3. Ước lượng bề rộng chữ Việt (Latin có dấu, đậm): pt*13 chứ không pt*11.
4. Model này không xem ảnh — verify bằng pdftotext + postcheck + python-docx
   (scripts/verify_bai0.py là khuôn).
5. Skill nói "add_toc_placeholders exit 0" là điều kiện cần nhưng KHÔNG đủ:
   phải soi XML xem có lặp mục không (postcheck không bắt lỗi này).

**Deliverable phiên 1:** projects/SPNC/deliverables/So_tay_hoc_tap_Bai_0.docx
(+ .pdf) — 8 trang, postcheck 0 lỗi, A4 hoàn tất.
