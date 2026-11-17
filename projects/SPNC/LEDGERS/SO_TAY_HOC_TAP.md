# SỔ TAY HỌC TẬP — tiến độ bài học (A4 duy trì)

> Mỗi bài: khái niệm dạy + trạng thái + file. Người dùng tự kiểm tra sau mỗi bài;
> trả lời sai → A4 dạy lại cách khác (không lặp nguyên văn).

| Bài | Nội dung | Trạng thái | File |
|---|---|---|---|
| 0 | Đề tài hỏi gì; 3 RQ (bao nhiêu → cái gì → tại sao); khung 6 nhóm yếu tố; thang đo là gì; vai trò người dùng | HOÀN TẤT 2026-11-17 | deliverables/So_tay_hoc_tap_Bai_0.docx (+pdf) |
| 1 | Tài liệu nghiên cứu: bài báo bình duyệt vs luận án; DOI; 4 dấu hiệu nguồn yếu (ví dụ THẬT: Ferdowsi sót [insert location], IJRISS review 3 ngày, Wang đổi chiều thang, 2 nguồn không mở được); đọc bài báo 10 phút | HOÀN TẤT 2026-11-17 (phiên 2) | deliverables/So_tay_hoc_tap_Bai_1.docx (+pdf) |
| 2 | Thang Dong-20 chi tiết: 3 chiều, đảo điểm, khoảng điểm 20–100, các hệ số α của gốc | SẴN SÀNG DỮ LIỆU (bản gốc đã xác minh toàn văn phiên 5 — verify/dong2013/DONG20_nguyen_van.md); soạn khi người dùng muốn | — |
| 3 | Bộ 30 item: nhãn nguồn từng câu, thang Likert, vì sao "researcher-developed" | Kế hoạch phiên 2 (sau khi có bản nháp cũ) | — |
| 4 | Số liệu: mean, SD, Cronbach alpha, item-total, vì sao KHÔNG EFA | Kế hoạch phiên 3 | — |
| 5 | Phỏng vấn & phân tích chủ đề Braun & Clarke 6 bước; chọn mẫu 3 mức | Kế hoạch phiên 3 | — |

## Bài 0 — nội dung đã dạy (đối chiếu yêu cầu)

- 3 từ khóa đề tài: phiên dịch đuổi / lo âu tình huống / yếu tố gây lo âu (mỗi cái có ví dụ đời thường).
- RQ1/RQ2/RQ3 + bảng tóm tắt RQ ↔ công cụ ↔ kết quả; ví dụ số cụ thể từng RQ
  (62/100; 4,1 vs 3,2; 3,9 với 2 lời kể khác nhau).
- Vì sao thứ tự bao nhiêu → cái gì → tại sao (nhiệt kế / bản đồ / phóng viên).
- Thiết kế hỗn hợp giải thích tuần tự (giải thích thuật ngữ ngay tại chỗ).
- Khung 6 nhóm (bảng kèm ví dụ tiêu biểu mỗi nhóm) + ghi chú minh bạch cảnh báo
  Ferdowsi & Razmi (chỉ dùng khung, không dùng tần suất).
- Thang đo là gì; Dong-20 (20 câu, Likert 5 điểm, 20–100, α=.92 gốc) vs bộ 30
  ("researcher-developed, pending pilot validation" — nói thẳng, không gọi chuẩn hóa).
- Vai trò người dùng/GVHD; 3 thứ cần mang cho phiên sau (bản nháp cũ, thông tin học phần, câu hỏi GVHD).
- 3 câu tự kiểm tra + đáp án gợi ý.

## Bài học kỹ thuật của phiên (cho A4/GLM sau này)

- docx-js 9.15 + add_toc_placeholders.py XUNG ĐỘT: docx-js tự sinh mục TOC đầu
  (hyperlink + PAGEREF, w:dirty) → script chèn thêm gây LẶP. Giải pháp: KHÔNG chạy
  script; tự thêm outlineLvl vào styles.xml + updateFields vào settings.xml
  (làm trong scripts/postfix_bai0.py).
- Bìa R5: section bìa bắt buộc margin 0 (nếu quên, wrapper 16838 bị margin ép lại,
  tiêu đề wrap xấu). Ước lượng bề rộng chữ Việt Latin: pt*13 (pt*11 của skill là
  cho tiếng Anh; chữ Việt có dấu + đậm rộng hơn).
- Model GLM sandbox này không xem được ảnh (Read trả "[Media omitted]") — verify
  tài liệu bằng pdftotext + postcheck + python-docx (đã có scripts/verify_bai0.py).
