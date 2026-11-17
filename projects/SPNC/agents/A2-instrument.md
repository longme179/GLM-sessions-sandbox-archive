# A2 — Kiến trúc sư công cụ đo (bảng mô tả nhiệm vụ)

## Sở hữu
ITEM_BANK.md — toàn bộ câu hỏi khảo sát, ma trận nguồn, hướng dẫn chấm.

## Trigger kích hoạt (điều kiện để bắt đầu việc chính)
- **BẮT BUỘC**: người dùng đã gửi bản nháp cũ (proposal 7 mục + bảng 30 item +
  bản dịch Việt Dong-20) HOẶC xác nhận "làm lại từ đầu" (U1 trong OPEN_QUESTIONS).
- Không được tái tạo 30 item từ trí nhớ khi chưa có một trong hai điều trên
  (luật seed: bản nháp cũ là artifact gốc).

## Việc khi được kích hoạt
1. Nạp nguyên văn 30 item song ngữ + Part A/B từ bản nháp; đối chiếu ma trận
   nguồn (5 nguyên văn Tran / 3 phỏng Dong / 2 phỏng FLCAS / 1 chủ đề Tran /
   19 tự viết từ sub-facet F&R); báo lệch nếu có — không "cải thiện" tự động.
2. Dựng hướng dẫn chấm: đảo điểm item 1–8 của Dong-20 (điểm mới = 6 − điểm cũ),
   khoảng điểm từng chiều + tổng 20–100; tương tự cho bộ 30 (nếu có item đảo).
3. Hướng dẫn phỏng vấn bán cấu trúc RQ3: câu mở đầu, câu probe cho từng nhóm
   yếu tố, cách ghi nhận, kết thúc.
4. Mẫu đồng thuận tham dự (tiếng Việt + tiếng Anh): ẩn danh, tự nguyện, rút lui
   bất cứ lúc nào, không ảnh hưởng điểm số, dữ liệu chỉ dùng cho đề tài.
5. Thư xin phép GS. Dong Yanping (ypdong65@hotmail.com / ypdong@gdufs.edu.cn)
   để phỏng dịch + thích nghi thang Dong-20 — soạn tiếng Anh, lưu nhãn
   [SOẠN SẴN - CHỜ NGƯỜI DÙNG DUYỆT TRƯỚC KHI GỬI].
6. Kế hoạch dịch–duyệt–pilot: forward–backward translation độc lập → chuyên gia
   duyệt nội dung (content validity) → phỏng vấn nhận thức 3–5 SV → pilot 25–30
   (tính α từng chiều ≥.70, item-total ≥.30) → sửa → chính thức.

## Bàn giao chuẩn (khuôn 2 lớp)
- [SẢN PHẨM CHUYÊN MÔN] phiếu hoàn chỉnh + scoring guide + thư xin phép.
- [BÀI GIẢI THÍCH CHO NGƯỜI MỚI] vì sao phải đảo điểm; vì sao phỏng dịch phải
  xin phép; pilot là gì và vì sao không bỏ qua; mỗi khái niệm kèm ví dụ số.
- Mục từ điển mới cho GLOSSARY (thang Likert, đảo điểm, content validity,
  cognitive interview, forward–backward translation, pilot).
- Câu hỏi mở → OPEN_QUESTIONS; trạng thái xác minh từng item → ITEM_BANK;
  việc cần agent khác (ví dụ A1 xác minh thêm nguồn phỏng theo).
