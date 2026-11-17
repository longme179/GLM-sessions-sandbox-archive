# Journal — phiên GLM sandbox 7 (2026-11-17 chiều, tiếp nối phiên 6)

## Bối cảnh mở phiên

Người dùng nhận ra trọng tâm đúng của đề tài là **Anxiety-Provoking / Anxiety-Inducing
Factors** (tìm NGUYÊN NHÂN gây lo âu), không phải "mức độ lo âu" như các sản phẩm
phiên 6 đang nhấn. Yêu cầu bắt đầu lại + giao task cho Agent-1 (OpenCode trên máy
Fedora) qua vai trò Agent-2 (remote task orchestrator) theo spec đầy đủ người dùng
cung cấp.

## Tái khung nghiên cứu (D16) — chốt bởi Agent-2 từ quyết định người dùng

- RQ2' = câu hỏi TRUNG TÂM: yếu tố nào gây lo âu nhiều nhất, nhóm nào nổi bật —
  bộ 30 item là công cụ chính, đầu ra chính là bảng xếp hạng 6 nhóm.
- RQ1' = HỖ TRỢ: mức độ lo âu (Dong-20) — 2 vai trò: baseline bối cảnh + phân
  tầng chọn mẫu phỏng vấn high/mid/low.
- RQ3' = GIẢI THÍCH: vì sao các yếu tố xếp hạng cao gây lo âu — phỏng vấn 10–12.
- Không đổi: thiết kế hỗn hợp tuần tự, mẫu n≈80–120 + pilot 25–30, α≥.70 +
  item-total≥.30 + không EFA, timeline 16 tuần, 6 nhóm F&R, cơ cấu 30 item.
- Khuyến nghị G1 ĐỔI: giờ khuyến nghị giữ cả Dong-20 (A) bất kể sĩ số, vì cần
  điểm để phân tầng phỏng vấn; nếu buộc rút ngắn → phân tầng bằng tổng điểm
  bộ 30 item.

## Việc làm qua Agent-1 (OpenCode tunnel, client scripts/agent2_client.py)

- **A2-001 (DONE)**: Agent-1 cập nhật ledger trên host — D16 vào DECISION_LOG,
  G1 bổ sung lý do baseline+phân tầng, ITEM_BANK đánh dấu bộ 30 item là
  INSTRUMENT TRUNG TÂM, tạo LEDGERS/REFOCUS_FACTORS.md (~1 trang đủ mục).
  Agent-1 còn tự đồng bộ LEDGERS cấp gốc với projects/SPNC/LEDGERS (bổ sung D15
  còn thiếu). Evidence grep đầy đủ, marker [AGENT-1 DONE #A2-001].
- **A2-002 (đang chạy khi phiên đóng)**: săn toàn văn Chiang 2006 (ICAS 44 item)
  qua các đường mới; kết quả sẽ ghi SOURCE_REGISTRY; ICAS chỉ là background,
  không chặn tiến độ.

## Sản phẩm phiên 7 (đều đã tái định hướng theo D16)

1. **Deck 13 slide v2** — SPNC_progress_report_supervisor.pptx/.pdf. Tên đề tài
   mới trên bìa "Anxiety-Inducing Factors in Consecutive Interpreting…";
   slide 2 + 5 gắn role tag CENTRAL RQ2 / SUPPORTING RQ1 / EXPLAINING RQ3;
   slide 6 = bộ 30 item CORE INSTRUMENT (đổi chỗ với Dong-20); slide 7 Dong-20
   = BASELINE + INTERVIEW STRATIFICATION với card "Two supporting roles (D16)";
   slide 8 mục 3.5 sắp lại; slide 11 khuyến nghị Q1 đổi lý do theo D16; D16
   xuất hiện trên 9 slide; nhãn cũ (Instrument I/II, tên cũ) = 0. Audit 13/13
   PASS, pptx 13 slides + 13/13 notes tiếng Việt (630–780 ký tự).
2. **Sổ tay dự phòng v2 (docx+pdf, 10 trang)** — 24 thay đổi qua patch script:
   kịch bản 13 slide theo vai trò mới, Bảng 2 đổi vai trò Dong-20/F&R, Q&A 5.1
   viết lại ("Vai trò của Dong-20 khi đề tài tập trung vào yếu tố"), 5.5/5.9
   theo factors, 4.1 khuyến nghị G1 mới, subtitle đề tài mới. Postcheck 0 lỗi,
   footer 3 vùng, verify PASS (Bảng 3 ghi nhận quyết định nguyên vẹn).

## Quy trình & bài học

- Va chạm regex: patch dòng-theo-số-thứ-tự `^["N. ` bắt cả dòng Bảng 3 (trang
  ghi nhận) làm docx crash — fix bằng script fix_bang3.py chỉ quét khối sau
  tableTitle Bảng 3. Bài học: patch theo số thứ tự phải giới hạn phạm vi khối.
- Edit tool không khớp file trộn Unicode-thật + escape \uXXXX → dùng patch
  script Python (line-based) thay Edit cho file loại này.
- Chuỗi 'Khung TRUNG TÂM' bị pdftotext chèn line-break giữa 2 từ → verify
  chuỗi dài phải kiểm cả biến thể wrap (flat-space đã xử lý, nhưng 'Khung\nTRUNG'
  nằm giữa câu — thực ra flat đã khớp khi tra đúng vị trí; bài học: kiểm tra
  grep -o trước khi kết luận thiếu).

## Trạng thái cuối phiên

- Deliverables v2 synced host (md5 khớp 4/4): pptx 2cdc890f…, pdf deck
  277b14d2…, docx 70a2a8c8…, pdf sổ tay 71ea671b….
- Ledger mirror về archive: DECISION_LOG (D16), OPEN_QUESTIONS, ITEM_BANK,
  REFOCUS_FACTORS.md.
- Chờ: kết quả A2-002 (ICAS) — sẽ đọc transcript phiên sau; U1/U2 vẫn chờ
  người dùng; người dùng cần điền [Student name]/[Supervisor name] slide 1.
