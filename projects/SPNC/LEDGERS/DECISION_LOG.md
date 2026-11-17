# DECISION_LOG — Sổ quyết định (orchestrator duy trì)

> Mỗi quyết định: nội dung + lý do + ai duyệt + ngày. Quyết định "ĐÃ CHỐT"
> chỉ mở lại khi GVHD hoặc người dùng yêu cầu.

| # | Ngày | Quyết định | Lý do | Duyệt bởi | Trạng thái |
|---|---|---|---|---|---|
| D1 | phiên trước | 3 RQ: RQ1 mức độ lo âu (Dong-20 thích nghi) / RQ2 xếp hạng 6 nhóm yếu tố (bộ 30 item) / RQ3 giải thích bằng phỏng vấn 10–12 SV chọn theo mức cao–TB–thấp | Mức độ → nguồn gốc → giải thích; mỗi RQ một công cụ riêng | Người dùng (phiên trước) | ĐÃ CHỐT |
| D2 | phiên trước | Thiết kế hỗn hợp giải thích tuần tự (khảo sát trước → phỏng vấn sau) | Phỏng vấn giải thích kết quả định lượng, không phải khám phá mù | Người dùng (phiên trước) | ĐÃ CHỐT |
| D3 | phiên trước | Mẫu: SV năm 3 ngành Tiếng Anh HCMUE đã học học phần phiên dịch đuổi; n≈80–120 thuận tiện; pilot 25–30 | Khả thi trong 1 học kỳ; đúng đối tượng RQ | Người dùng (phiên trước) | ĐÃ CHỐT |
| D4 | phiên trước | Phân tích: mean+SD+xếp hạng; Cronbach's α từng chiều (≥.70) + item-total (≥.30); thematic analysis Braun & Clarke (2006); KHÔNG EFA với n≈100 | n quá nhỏ cho EFA ổn định; α từng chiều đủ bảo vệ độ tin cậy | Người dùng (phiên trước) | ĐÃ CHỐT |
| D5 | phiên trước | Cơ cấu bộ 30 item: 5 nguyên văn Tran + 3 phỏng theo Dong + 2 phỏng theo FLCAS + 1 từ chủ đề thảo luận Tran + 19 tự viết từ sub-facet F&R | Phủ 6 nhóm × 5 câu; ghi nhãn nguồn từng item | Người dùng (phiên trước) | ĐÃ CHỐT |
| D6 | 2026-11-17 | Khi gateway OpenCode 401: DỪNG thử lại (đúng kỷ luật archive), chạy A1–A5 bằng sub-agent nội bộ của sandbox, mirror kết quả vào repo này; chờ người dùng cấp lại mật khẩu | Nghiêm cấm đoán/brute-force mật khẩu; sản phẩm không được đứng chờ | Orchestrator (phiên 1) | ĐÃ CHỐT |
| D7 | 2026-11-17 | A4 viết Bài 0 (bài học mở đầu) trực tiếp từ seed (3 RQ + khung 6 chiều + "thang đo là gì"), không đợi A1 | Người dùng cần nền kiến thức NGAY theo yêu cầu "bước đầu tiên" | Orchestrator (phiên 1) | ĐÃ CHỐT |
| D8 | 2026-11-17 | Chờ người dùng: (a) bản nháp cũ (proposal 7 mục, bảng 30 item, bản dịch Việt Dong-20) → nạp làm artifact gốc; (b) handbook HCMUE. Chưa có → tái tạo từ seed và xin xác nhận | Luật seed: bản nháp cũ nếu có luôn là artifact gốc ưu tiên | Orchestrator (phiên 1) | CHỜ NGƯỜI DÙNG |
