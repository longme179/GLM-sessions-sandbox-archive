# Journal — Compendium trích 11 framework (2026-11-19, phiên 2)

## Nhiệm vụ
"Nghiên cứu, tổng hợp, trích lại các frameworks của các bài nghiên cứu trên"
→ tài liệu tiếng Anh trích nguyên văn + hệ thống hoá 11 framework đứng sau
đề tài, giữ trọng tâm factors (không trôi sang levels).

## Nguồn trích (100% từ kho verified của project, không đoán)
- FLCAS 33 item (FLCAS.pdf) — 3 thành phần; item 2,8,9,13,20,24,27,30,33 nguyên văn
- ICAS 44/44 item (LEDGERS/ICAS_ITEMS.md, Appendix A tr.203–205, UMI 3249927)
  — 3 nhân tố PCA α .92/.80/.77, 40,9% variance, n=306, M=147.6, SD=22.1
- Dong-20 (verify/dong2013/DONG20_nguyen_van.md, CNKI md5 a27ab518...) —
  3 chiều 6/7/7 item, item 1–8 đảo điểm; α .92/.91/.84; r −.434/−.417/−.269;
  2 item trích nguyên văn tiếng Trung (16, 9)
- F&R 2024 (fulltext HTML) — 6 nhóm + tần suất ĐẦY ĐỦ: individual 36, input 30,
  note-taking 24, output 18, environmental 15, teacher 12 (bài gốc mislabel
  rank 4; đếm thực tế output 18 > environmental 15)
- Tran 2025 — 5 item nguyên văn + M 3.87/3.87/3.78/3.78/3.57
- Hoang & Ho 2026 (PDF) — ILA = FLA components × Gile EM; 4 chiều + α + ranking
- Sabrina 2025 (PDF) — 4 factors + % + impact taxonomy
- Chang 2016 (abstract) — 5 subscales 34→21 items (không trích số liệu)
- Li & Zhu 2026 (abstract) — task-intrinsic vs social-evaluative + familiarity
- Xing 2025 — ID network; IAS portability
- Magušar-Marton 2026 (abstract) — nonverbal cues

## Sản phẩm
Research_Frameworks_Compendium_Anxiety_CI.docx (+PDF), 18 trang tiếng Anh:
- Ch1: purpose/method/quotation policy + Table 1 (11 frameworks × tier × status)
- Ch2: 3 foundational scales trích chi tiết (construct/dimension/instrument/
  evidence/role) + 3 bảng extract
- Ch3: 5 classification frameworks + 4 bảng (F&R freqs, Tran 5 item kèm map,
  ILA 4 dims, Sabrina 4 factors)
- Ch4: 3 partial lenses
- Ch5: Table 8 ma trận 6 nhóm HCMUE × 6 cột framework (7 hàng gồm pre-task);
  lineage FLCAS→ICAS→IAS→Chang→F&R→(gap)→HCMUE; 3 bất đồng giữa framework
  = cơ hội đề tài (ranking, coverage preparation, mechanism).
Postcheck 0 lỗi; 18 trang không trang trắng; 27/27 content checks (2 probe
false-positive do pdftotext bỏ hyphen cuối dòng — xác minh bằng regex flex).

## Sửa kèm
Litreview docx: sửa lỗi Xing 2025 — r=.711 là proficiency↔performance
(không phải anxiety↔performance); regen + verify. Sync host md5 OK 4/4.

## File
- scripts/gen_frameworks_{base,part2,part3,main}.js
- download/Research_Frameworks_Compendium_Anxiety_CI.{docx,pdf}
