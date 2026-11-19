# Original Papers — Bản gốc các nghiên cứu đã dùng làm dữ liệu

> Ngày gom: 2026-11-19. Mọi file đã được kiểm tra (định dạng PDF thật, số trang,
> nội dung trang 1 khớp định danh bài báo). Đây là bản lưu phục vụ trích dẫn học
> thuật của dự án SPNC (HCMUE); bản quyền thuộc các tác giả/nhà xuất bản.

## Đã tải thành công (11 file)

| File | Nguồn | Ghi chú |
|---|---|---|
| `Horwitz_Horwitz_Cope_1986_MLJ_article.pdf` | Ohio State mirror của bản JSTOR (bản scan 9 trang) | **Bài gốc MLJ 70(2):125–132** — tải mới phiên này |
| `Horwitz_1986_FLCAS_scale_instrument.pdf` | dept.english.wisc.edu | Thang FLCAS 33 item (instrument), đã verify từ trước |
| `Dong_Chen_Yu_2013_IAS_CNKI.pdf` | CNKI (người dùng tải 17/11/2026, md5 a27ab518...) | Bài gốc tiếng Trung 外语界 2013/6:57–64, có phụ lục thang 20 item |
| `Chiang_2010_Meta_article_Erudit.pdf` | Érudit (open) | Bài Meta 55(3) — nghiên cứu cùng tác giả ICAS, dùng dẫn chứng thứ cấp |
| `Chiang_2006_AppendixA_ICAS44_reconstructed.txt` | attachments.academia-assets.com (18 trang render công khai, HTML 217–234 = printed 203–220) | **Tái dựng từ các trang HTML công khai** của luận án; đủ 44/44 item ICAS (đã đối chiếu với ICAS_ITEMS.md). PDF gốc ProQuest/Academia bị login gate |
| `Ferdowsi_Razmi_2024_fulltext_HTMLcapture.txt` | sflj.springeropen.com (bản capture toàn văn HTML) | **Toàn văn bài báo** (text đầy đủ, kể cả Table 1 frequencies); PDF trực tiếp bị Cloudflare challenge |
| `Tran_2025_IJRISS.pdf` | rsisinternational.org Digital Library | **Tải mới phiên này** — 10 trang, đúng DOI 10.47772/IJRISS.2025.903SEDU0335 |
| `Hoang_Ho_2026_CTTLE.pdf` | cttle.org (open) | Toàn văn 13, DOI 10.51287/cttle20263 |
| `Sabrina_2025_IJELR.pdf` | jurnal.umsu.ac.id (open) | Toàn văn IJELR 7(1):117–132 |
| `Xing_2025_HSSC_Nature.pdf` | nature.com (open access) | **Tải mới phiên này** — 1.36MB, HSSC 12:1449 |
| `Wang_2025_Frontiers_Psychology.pdf` | frontiersin.org (open access) | **Tải mới phiên này** — Front. Psychol. 16:1671239 |

## Không tải được PDF — link chính thức để tự tải bằng trình duyệt

| Nghiên cứu | Lý do thất bại | Link chính thức |
|---|---|---|
| **Ferdowsi & Razmi 2024** (PDF) | Springer/Open trả "Client Challenge" (Cloudflare) cho mọi biến thể `sflj.springeropen.com`, `link.springer.com`, `d-nb.info` timeout | https://sfleducation.springeropen.com/articles/10.1186/s40862-024-00260-6 (bấm "Download PDF"; bài CC-BY 4.0) |
| **Chiang 2006** (luận án toàn văn PDF) | Academia.edu login gate; ProQuest cần tài khoản; UT Repository 403 | https://www.academia.edu/85280917 (bản đọc công khai 268 trang); ProQuest UMI 3249927; https://hdl.handle.net/2152/2695 |
| **Chang 2016** (T&I Review) | KCI là SPA cần phiên trình duyệt; không có mirror mở | http://journal.kci.go.kr/erits/archive/articleView?artiId=ART002609369 (bấm nút PDF trong trang) |
| **Li & Zhu 2026** (IJAL Wiley) | Cloudflare "Just a moment..." chặn curl; pdfdirect trả challenge | https://onlinelibrary.wiley.com/doi/10.1111/ijal.70348 (OA, bấm "PDF" trên trang bài) |
| **Magušar-Marton 2026** (Acta Univ. Sapientiae) | Host `acta.sapientia.ro` và `sciendo.com` không kết nối được từ sandbox (timeout/404) | https://acta.sapientia.ro/content/docs/11-531026.pdf (đường dẫn PDF thật do DOI resolve); DOI 10.47745/ausp-2025-0023 |
| **Song et al. 2026** (JPR Wiley) | Không OA (Unpaywall: is_oa = false) | https://doi.org/10.1111/jpr.70033 (cần đăng ký/thư viện) |

## Ghi chú

- `Chiang_2006_AppendixA_ICAS44_reconstructed.txt` là bản tái dựng **chữ** từ 18
  trang HTML render công khai (giữ nguyên đánh số item, kể cả lỗi in `[sic]`
  của bản gốc). Nó thay thế PDF cho mục đích trích dẫn 44 item; file
  `ICAS_ITEMS.md` trong LEDGERS là bản đối chiếu đã kiểm.
- `Ferdowsi_Razmi_2024_fulltext_HTMLcapture.txt` là toàn văn (kể cả bảng)
  dạng text — đủ cho trích dẫn; PDF chỉ cần cho trình bày đẹp.
- Horwitz 1986: bản OSU là bản scan JSTOR 9 trang (cover page JSTOR + 8 trang
  bài); dùng kèm thang FLCAS trong file instrument.
