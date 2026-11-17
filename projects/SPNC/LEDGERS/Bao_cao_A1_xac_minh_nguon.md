# BÁO CÁO A1 — Xác minh nguồn (phiên 2026-11-17)

> Phương pháp: mọi nguồn mở thật bằng WebFetch/curl + pdftotext trong phiên; không dùng trí nhớ để "xác minh". Bằng chứng: `download/source-verification-evidence/` (FLCAS.pdf, ferdowsi2024_fulltext.txt, ferdowsi2024_table1.html, wang2025_frontiers_fulltext.xml, ghorbani2025.pdf, adwen.pdf, appendix4_anxiety.docx).

## Trạng thái từng nguồn

| Nguồn | Trạng thái | Đã xác minh | Cảnh báo |
|---|---|---|---|
| Ferdowsi & Razmi 2024, APSFLE 9:38, DOI 10.1186/s40862-024-00260-6 | ĐÃ MỞ TOÀN VĂN | 6 nhóm + sub-factor (individual: general anxious feelings, low concentration, perfectionism, introversion; input: language + speaker; note-taking: skill + creativity; environmental: noise + peer presence; output: meaning transfer + delivery; teacher: testing/scoring + behavior). CC-BY 4.0. 30 SV, 5 focus group | Lỗi biên tập: sót "[insert location]", câu lặp, Table 1 sai thứ tự (Environmental 15 trước Output 18 dù ghi "highest to lowest"), typo, trích Chiang (2010) không có trong reference. Chỉ dùng khung khái niệm |
| Tran 2025, IJRISS 9(3):4652–4661, DOI 10.47772/IJRISS.2025.903SEDU0335 | ĐÃ MỞ TOÀN VĂN | 5 item nguyên văn + mean khớp 100% (3.87/3.87/3.78/3.78/3.57). Bối cảnh: Thai Nguyen University, 63 SV, chiều Anh–Việt, khung Krashen + Gile | KHÔNG có DOAJ; review 3 ngày; missing references (Danielson 2021, Durante 1999); citation mismatches. Chỉ dùng làm bối cảnh VN |
| Wang 2025, Front. Psychol. 16:1671239, DOI 10.3389/fpsyg.2025.1671239 | ĐÃ MỞ TOÀN VĂN | Dùng thang Dong 2013; Q2 chấm ngược; MẪU 47 SV năm 3 (Shanghai Dianji Univ, 9/2024–1/2025); task anxiety giảm 3.47→3.20 (p=.043) sau nhật ký phản tư Gibbs | ĐỔI TÊN + TỰ GẮN LẠI chiều (task/error/confidence; chỉ gán 13/20 item); KHÔNG báo cáo α. Không trích Wang làm nguồn cấu trúc gốc Dong |
| Dong, Chen & Yu 2013, Foreign Language World (6):57–64 | KHÔNG MỞ ĐƯỢC [CHƯA XÁC MINH phần lớn] | Qua snippet PDF RG: 3 chiều 艰巨性/服务性/一般自信; α=.92 xuất hiện trong snippet | Cần mạng thường/máy thật tải RG hoặc CNKI. Mọi con số khác (n=245, pilot .91, retest .84, r −.434/−.417/−.269, item mean 3.27, phân bổ item) GIỮ [CHƯA XÁC MINH] |
| Horwitz et al. 1986, MLJ 70(2):125–132 (FLCAS) | ĐÃ MỞ TOÀN VĂN THANG ĐO | Đủ 33 item nguyên văn (đã kiểm đếm bằng code). Item sợ đám đông: #9, 13, 20, 24, 31, 33 (nguyên văn trong FLCAS.pdf) | α=.93 CHƯA xác minh (PDF chỉ là thang đo, cần bài gốc MLJ) |
| Chiang 2006, UT Austin, hdl 2152/2695 | KHÔNG MỞ ĐƯỢC PDF [CHƯA XÁC MINH item] | Secondhand (Ghorbani & Ferdowsi 2025, đã mở toàn văn): ICAS 44 item, Likert 5, có item đảo; 3 chiều: fear of interpretation and negative evaluation (α .92) / cognitive processing anxiety (.80) / low self-confidence (.77); tổng α .94. 5 nguồn lo âu (snippet): speaker, audience, self, task, classroom procedures | ≥10 đường bị chặn (UT DSpace 403, hdl, jina, webcache, archive.org, core, academia...). Cần trình duyệt thật: repositories.lib.utexas.edu/items/9436dca1-6928-48c2-92ef-7bdb8d264421. Fallback: Appendix B luận án Bates 2016 (KU) — bản adapted ICAS |

## FLCAS — item nguyên văn về nói trước đám đông / sợ đánh giá

- #9: "I start to panic when I have to speak without preparation in language class."
- #13: "It embarrasses me to volunteer answers in my language class."
- #20: "I can feel my heart pounding when I'm going to be called on in language class."
- #24: "I feel very self-conscious about speaking the foreign language in front of other students."
- #31: "I am afraid that the other students will laugh at me when I speak the foreign language."
- #33: "I get nervous when the language teacher asks questions which I haven't prepared in advance."

## Nghiên cứu 2024–2026 mới

1. Wang (2025) Front. Psychol. — nhật ký phản tư giảm task anxiety (chi tiết ở bảng trên).
2. Xing (2025) Humanities & Social Sciences Communications (Nature Portfolio), DOI 10.1057/s41599-025-05821-9 — 64 SV Trung Quốc; r hiệu suất–ngôn ngữ .711; lo âu ảnh hưởng tiêu cực. Uy tín cao.
3. Song et al. (2026) Japanese Psychological Research (Wiley), DOI 10.1111/jpr.70033 — eye-tracking + GSR, dùng thang Dong; lo âu tự báo dự báo mạnh hơn đo sinh lý.
4. Ghorbani Payborj & Ferdowsi (2025) Applied Linguistics Inquiry 3(2):131–141, DOI 10.22077/ali.2025.9244.1134 — ICAS + disfluency (Praat), 23 SV Iran. Tạp chí nhỏ, dùng để trích mô tả ICAS.
5. Jiang (2026) [CHƯA XÁC MINH] — ScienceDirect chặn; PII S000169182600630X, khả năng Acta Psychologica. Cần follow-up trước khi cite.

## Việc tiếp theo

1. Dong 2013 + Chiang 2006: cần người dùng mở bằng trình duyệt thật (link trong bảng) rồi gửi PDF vào upload/.
2. FLCAS α=.93: truy bài gốc MLJ 1986 (Wiley/thư viện).
3. A2 đối chiếu item phỏng theo FLCAS với 6 item nguyên văn ở trên.
