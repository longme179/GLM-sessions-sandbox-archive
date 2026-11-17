# Journal — phiên GLM sandbox 5 (2026-11-17 chiều, tiếp nối phiên 4)

## Bối cảnh mở phiên

Người dùng trả lời đúng việc "PDF" trong danh sách chờ của phiên 4: tải lên 2 tệp
— `dong 2013.pdf` và `chiang.pdf` (kèm một bản sao trùng md5 `045079ar.pdf`).
Đây là 2 nguồn mà các phiên 1–3 đã thử ≥15 đường khác nhau đều bị chặn.

## Xác minh — kết quả lớn nhất từ trước tới nay

1. **Dong 2013 ĐÃ XÁC MINH TOÀN VĂN, khớp 100%**: bản CNKI 8 trang, toàn văn
   tiếng Trung trích xuất sạch. Từng con số đối chiếu với seed: 3 chiều
   巨大性(3,5,7,15,16,20)/服务性(4,6,9,10,11,12,14)/一般自信(1,2,8,13,17,18,19),
   α=.92 (n=245), pilot .91 (n=25), test–retest α=.84 (n=60), r=−.434/−.417/−.269
   (n=56), item mean 3.27/3.16, item 1–8 tích cực → đảo điểm. 20 item nguyên văn
   đủ ở phụ lục tr.64 → lưu `verify/dong2013/DONG20_nguyen_van.md` (cột Hán
   nguyên văn + dịch tham khảo Việt + chiều + hướng).
   Chi tiết hình thức đáng nhớ: bản gốc báo cáo retest là **α .84, không phải
   r .84** như mô tả thông dụng — trích đúng theo bản gốc.
2. **Phát hiện hiểu sai Q10**: tóm tắt cũ ghi "Q10 = bối cảnh hành nghề". Nguyên
   văn Q10 = sợ hai bên được phục vụ (hiểu chút ngôn ngữ nhau) phát hiện lỗi —
   fear of negative evaluation thuần túy. → G5 viết lại: GIỮ item, chỉ thích
   nghi bối cảnh "hai bên được phục vụ" → "giảng viên và bạn học" (OPEN_QUESTIONS
   đã cập nhật, chờ duyệt).
3. **chiang.pdf KHÔNG phải luận án 2006** — là bài báo Chiang (2010) Meta 55(3)
   DOI 10.7202/045079ar (213 SV Đài Loan, FLCAS + TAI). ICAS nguyên văn (S6) vẫn
   CHƯA XÁC MINH; UT repository vẫn 403. Giá trị thu được từ bài 2010:
   FLCAS α=.93 (n=108) + retest r=.83 (n=78) xác nhận gián tiếp; bản Trung FLCAS
   α=.94 trên SV phiên dịch; FL anxiety r=−.313/−.362 với điểm thi (khống chế
   trait vẫn −.252/−.307) trong khi trait anxiety không tương quan — luận cứ
   ủng hộ thang tình huống; 24/33 & 28/33 item FLCAS tương quan âm; NOTE 2: các
   lớp tập trung phiên dịch đuổi. Email tác giả công khai: yungnan2@yahoo.com.
4. **Đính chính S1 (F&R 2024)**: ghi chú cũ "trích Chiang 2010 thiếu reference"
   là SAI — F&R CÓ đủ references Chiang 2006/2009/2010 (grep toàn văn). Hai lỗi
   thật thay thế: câu hỏng "which demonstrates which reveals"; quy công phát
   hiện noise (Gerver 1974) cho Chiang 2010. Bài học: ghi chú "thiếu X" phải
   kiểm tra bằng tra cứu định dạng-tolerant trước khi ghi sổ.

## Sổ đã cập nhật (D15)

- SOURCE_REGISTRY: S4 → ĐÃ XÁC MINH TOÀN VĂN; S6 → làm rõ + 2 con đường còn lại;
  S1 → đính chính references + 2 lỗi thật; nguồn mới: Chiang 2010 (đầy đủ).
- DECISION_LOG D15; ITEM_BANK Part B (Q10 + chuẩn dịch); OPEN_QUESTIONS G5;
  GLOSSARY (bài học trộn lẫn tài liệu cùng tác giả); SO_TAY (Bài 2 sẵn dữ liệu).

## Bài học phiên này

- **Săn nguồn: đường người dùng-tải-trình-duyệt luôn thắng**: 15+ đường bot bị
  chặn (phiên 1–3) vs 1 lần người dùng tải thủ công là xong toàn bộ. Kể từ đây,
  mọi nguồn "CHƯA XÁC MINH vì bị chặn" → ưu tiên liệt kê URL chính xác + hướng
  dẫn tải cho người dùng thay vì thử thêm đường bot.
- **Cùng tác giả ≠ cùng tài liệu**: Chiang 2006 (luận án, ICAS) / 2009 / 2010
  (Meta, FLCAS) — trộn lẫn là lỗi trích dẫn thật. Luôn đối chiếu TỰA ĐỀ + nhà
  xuất bản của file nhận được với định danh nguồn trong sổ, ngay cả khi tên
  file "đúng".
- **Sửa file bằng replace toàn cục nguy hiểm**: lần sửa DONG20 lần đầu, replace
  "口译"→"phiên dịch" đã làm bẩn CẢ cột nguyên văn (chính thứ phải bảo toàn).
  May kiểm tra ngay sau đó phát hiện. Luật rút ra: với file có cột "nguyên văn
  chuẩn", không bao giờ edit bằng find-replace toàn cục — viết lại nguyên khối.
- Postfix docx phiên 5 chạy heredoc inline (vi phạm luật lưu script) — đã bổ
  sung lưu `postfix_baocao_phien5.py` ngay sau đó. Không lặp lại.

## Sản phẩm phiên 5

- **Báo cáo phiên 5** (docx + pdf, 9 trang, 8 mục, 3 bảng, bảng 20 item nguyên
  văn tiếng Hán font Noto Serif SC): verify PASS (thứ tự, 20/20 tiền tố Hán,
  mã bài 1004-5112, DOI, α, n, r, D15, G5), postcheck 0 lỗi, footer 3 vùng chuẩn.
- Evidence: verify/dong2013/ (PDF CNKI + fulltext + DONG20_nguyen_van.md),
  verify/chiang2010/ (PDF Érudit + fulltext).

## Trạng thái cuối phiên

- 5/6 nguồn seed hết CHƯA XÁC MINH (S6 ICAS item nguyên văn là phần còn lại;
  mọi số liệu dùng trong phiếu/Chương 3 đều đã có bản gốc đứng sau).
- Chờ người dùng: duyệt G5 mới, U1 (bản nháp cũ), U2 (học phần), U4 (ưu tiên
  Bài 2 sổ tay vs proposal); tùy chọn: ProQuest hoặc thư gửi Chiang.
- Hạ tầng: gateway 200 ổn định xuyên phiên (fs/shell đã từng dùng ở phiên 4;
  phiên này chưa cần — mọi việc làm trong sandbox).
