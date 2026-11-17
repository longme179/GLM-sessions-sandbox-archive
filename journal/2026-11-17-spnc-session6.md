# Journal — phiên GLM sandbox 6 (2026-11-17 chiều, tiếp nối phiên 5)

## Bối cảnh mở phiên

Người dùng đặt tình huống: giảng viên hướng dẫn có thể gọi họp và yêu cầu báo cáo
tiến độ ngay, "chưa có gì" trong cảm nhận — nhưng thực tế dự án đã có rất nhiều.
Nhiệm vụ: trình bày ý tưởng, kế hoạch SPNC từ toàn bộ dữ liệu đã có.

## Sản phẩm phiên 6

1. **Bộ slide báo cáo tiến độ 13 trang (EN + speaker notes VN đầy đủ)** —
   `SPNC_progress_report_supervisor.pptx` (+ PDF backup). Phong cách "Scholarly
   Navy" (parchment/navy/brass, Playfair + Source Serif 4 + Inter), không ảnh,
   dữ liệu + bảng. Cấu trúc: bìa → agenda+3RQ → 6 nguồn → kỷ luật xác minh
   (5/6, 20/20, 100%, D1–D15) → thiết kế RQ↔công cụ↔phân tích → Dong-20 (đủ số
   liệu tâm trắc) → bộ 30 item (6 nhóm, 30=5+3+2+1+19) → Chương 3 nháp + phân
   tích (không EFA) → timeline 16 tuần → 8 sản phẩm đã giao → 4 quyết định cho
   GVHD (G1/G5/G7/G8) → rủi ro + phương án → next steps 2 tuần.
   Quy trình đúng skill ppt: Stage 3 (global.css + slides_brief.json tự viết,
   13 task_brief self-contained với notes_must_include) → Stage 4 fan-out 3
   sub-agent (0:5, 5:9, 9:13) → export batch_html2pptx.js 0 cảnh báo →
   audit Playwright 13/13 PASS (1280×720, 0 phần tử tràn, 0 chữ cắt, 13/13
   notes 741–988 ký tự) → pptx verify 13 slides + 13/13 notes bằng python-pptx.
   Lưu ý render: môi trường không xem được ảnh → visual check thay bằng audit
   code đo hình học thực (scripts/audit_slides.js) + verify số liệu trên HTML
   nguồn (α=.92 ×3, 245 ×4, r ×2, D1–D15 ×2...).
2. **Sổ tay dự phòng buổi họp (docx+pdf, 9 trang, VN)** —
   `Sotay_du_phong_buoi_hop_GVHD.docx`. Khuôn R5 + 3 section như mọi báo cáo
   SPNC. Nội dung: (1) cách dùng + kịch bản rút 3 phút; (2) bảng kịch bản 13
   slide × thời lượng × ý chính × câu chuyển; (3) bảng số liệu tra nhanh mọi
   nguồn; (4) 4 quyết định A/B + khuyến nghị; (5) 10 câu hỏi đáp dự phòng
   (tại sao Dong-20 không FLCAS, vì sao không EFA, vì sao khảo sát trước...);
   (6) checklist vật dụng + trang ghi nhận quyết định để điền tại bàn.
   Verify: postcheck 0 lỗi (1 warning line-spacing do mật độ bảng — chủ đích),
   footer 3 vùng chuẩn (bìa/I/1–7), thứ tự 6 mục + 17 heading PASS, mọi số liệu
   then chốt có mặt, 0 token xấu.

## Quyết định mặc định đã chọn (không hỏi được — ghi rõ để người dùng đổi)

- Deck TIẾNG ANH (ngôn ngữ ngành/khóa luận) + notes tiếng Việt (người dùng đọc
  Presenter View); sổ tay tiếng Việt (cầm tay đọc nhanh).
- 13 slide (đủ nội dung cho 10–12 phút, không quá dài cho buổi họp GVHD).
- Slide 1 giữ placeholder [Student name]/[Supervisor name] — đã ghi rõ trong
  checklist 6.2 phải thay trước khi trình chiếu.
- Phong cách học thuật hàn lâm, không ảnh (dữ liệu/bảng), đúng chuẩn skill.

## Liên kết sổ

- 4 quyết định trên slide 11 = G1/G5/G7/G8 OPEN_QUESTIONS (không đổi trạng thái
  — vẫn chờ GVHD; slide chỉ trình bày).
- Bảng số liệu = SOURCE_REGISTRY + DONG20_nguyen_van.md (phiên 5), không số mới.
- Timeline = G8-A; rủi ro = phương án 1-B/8-B đã có sẵn trong OPEN_QUESTIONS.

## Bài học phiên này

- Skill ppt trong listing ghi base `/home/z/my-project/skills/pptx` (thư mục
  `pptx`) — SKILL.md ghi path `skills/ppt/...` sai; mất 1 lệnh tìm lại. Ghi
  nhớ cho các phiên sau: dùng `find` ngay khi MODULE_NOT_FOUND.
- Bash env prefix (OC_URL=... cmd) KHÔNG truyền biến vào lệnh `timeout` thứ 2+
  trong cùng chuỗi — phải `export` (lỗi này đã gặp phiên 5 khi chunk PDF).
- Read ảnh trong môi trường này không hiển thị (model không nhận image input)
  → visual check slide thay bằng audit hình học Playwright + pdftotext; đủ
  mạnh để bắt overflow/mất chữ, và cheap hơn re-render.

## Trạng thái cuối phiên

- Deliverables phiên 6: SPNC_progress_report_supervisor.pptx/.pdf,
  Sotay_du_phong_buoi_hop_GVHD.docx/.pdf, slides/ (13 HTML + css + brief).
- Đã sync toàn bộ lên host ~/Documents/SPNC (md5 khớp) + push archive.
- Chờ người dùng: duyệt G5 mới, U1, U2, U4 (như phiên 5) + điền tên thật
  slide 1 trước buổi họp.
