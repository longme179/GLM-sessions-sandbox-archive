# Journal — Tải bản gốc các nghiên cứu (2026-11-19, phiên 3)

## Nhiệm vụ
Tải PDF bản gốc từng nghiên cứu đã dùng làm dữ liệu; bài nào thất bại thì đưa link chính thức.

## Kết quả tải mới (phiên này)
- Horwitz 1986 bài gốc MLJ 70(2):125–132 — bản scan JSTOR 9 trang qua mirror
  ling.ohio-state.edu/research/groups/lacqueys/readings/horowitz.pdf (1.19MB)
- Tran 2025 IJRISS — rsisinternational.org Digital Library, 10 trang, DOI khớp
- Xing 2025 HSSC Nature — nature.com/articles/s41599-025-05821-9.pdf (1.36MB)
- Wang 2025 Frontiers — frontiersin.org PDF (11 trang)
- Chiang 2006 Appendix A — tái dựng lại từ 18 trang render công khai
  attachments.academia-assets.com/90027180/{217..234}.html; đủ 44/44 item,
  đối chiếu 3 câu chốt với ICAS_ITEMS.md OK (script
  scripts/rebuild_chiang_appendix.py)

## Có sẵn từ trước (gom về original_papers/)
FLCAS scale PDF, Dong 2013 CNKI, Chiang 2010 Meta (Érudit), Hoang&Ho 2026,
Sabrina 2025, Ferdowsi 2024 fulltext HTML capture.

## Thất bại (link chính thức đã đưa trong README)
- Ferdowsi 2024 PDF: Cloudflare Client Challenge mọi host Springer; d-nb.info timeout
  → https://sfleducation.springeropen.com/articles/10.1186/s40862-024-00260-6
- Chiang 2006 toàn văn: Academia login gate, ProQuest cần tài khoản
  → https://www.academia.edu/85280917 / ProQuest UMI 3249927
- Chang 2016: KCI SPA cần session trình duyệt
  → http://journal.kci.go.kr/erits/archive/articleView?artiId=ART002609369
- Li&Zhu 2026: Wiley Cloudflare "Just a moment..."
  → https://onlinelibrary.wiley.com/doi/10.1111/ijal.70348 (OA)
- Magušar-Marton 2026: acta.sapientia.ro + sciendo.com không kết nối từ sandbox
  → https://acta.sapientia.ro/content/docs/11-531026.pdf (DOI resolve được)
- Song 2026 JPR: không OA → https://doi.org/10.1111/jpr.70033

## Verify
9 PDF probe trang 1 OK (Tran probe MISS do dấu ' U+2019 — thủ tục, file chuẩn);
số trang: Horwitz 9, FLCAS 5, Dong 8, Chiang2010 14, Tran 10, Hoang 11,
Sabrina 16, Xing 17, Wang 11. Sync host 12/12 md5 OK (mkdir original_papers trước).
