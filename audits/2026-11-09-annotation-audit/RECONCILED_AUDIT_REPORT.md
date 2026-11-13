# BÁO CÁO ĐỐI CHIẾU — AUDIT ẢO GIÁC ANNOTATIONS (2 TUYẾN ĐỘC LẬP)

**Ngày:** 2026-11-09 · **Nhánh:** `docs/annotate-and-map` (base `6c1dc3c`, HEAD `53e2c15`)
**Tuyến 1:** GLM (tự audit) — replica local byte-exact (md5 `9ad76af...`), parser + grep + battery độc lập
**Tuyến 2:** Agent **Beam (Max)** — `beam` @ ollama-cloud, variant `max`, session OpenCode riêng `ses_e40ba3b11ffetYsL1bdSeobvHg`, không được tiếp xúc kết quả Tuyến 1
**Trọng phúc phân kỳ:** grep lại trên MÁY THẬT qua bridge worker (session `1e23f2bc...`)

## 1. Kết quả song song

| Hạng mục | Tuyến 1 (GLM) | Tuyến 2 (Beam Max) |
|---|---|---|
| REL tags kiểm | 108 dòng tag / ~180 tham chiếu | 108 tags |
| REL sạch | 103 | 103 PASS |
| REL lỗi thật | 5 (2 FAIL + 3 symbol) | 2 FAIL + 3 PARTIAL |
| INVARIANT | 26/26 ĐÚNG | 26/26 PASS |
| GOTCHA | 10/10 ĐÚNG | 10/10 PASS |
| Map file:line refs | 34/34 in-bounds | 55/55 resolved + in-bounds |
| Map nội dung anchor | ~40 khớp, 1 cụm lệch dòng | sampled khớp, 1 offset note |
| Comments-only (không đổi hành vi) | AST 276/276 + stripper 153/153 + sh 14/14 | inspect hunks — xác nhận |
| Đường dẫn REL | 180/180 tồn tại | all resolved tồn tại |

→ **Hai tuyến độc lập hội tụ gần tuyệt đối** (cùng đếm 108 tags, cùng 103 sạch, cùng 36/36 INVARIANT+GOTCHA đúng, cùng xác nhận comments-only).

## 2. Các lỗi ĐÃ XÁC NHẬN (thứ hạng chung sau trọng phúc)

| # | Vị trí | Lỗi | Phát hiện bởi | Trọng phúc |
|---|---|---|---|---|
| 1 | qml/services/ControlRegistry.qml:2 | Symbol bịa `read_control_grid` — không tồn tại; control-grid.json thật ra do `legacy_ids()`/`load_catalog()` đọc | CẢ HAI (nhất trí) | grep chỉ match chính dòng annotation |
| 2 | qml/settings/SettingsRegistry.qml:3 | `openPage` ghi `SettingsView.qml` — thật: `SettingsApplication.qml:23` (IpcHandler) | CẢ HAI (nhất trí) | grep xác nhận |
| 3 | qml/panels/ControlDashboard.qml:217 | `"powerProfile"` ghi `audio_actions.py` — thật: `desktop_backend.py:1422/1475` | **GLM** (Beam bỏ sót) | máy thật: audio_actions RC=1, desktop_backend:1422 ✓ |
| 4 | scripts/deploy_niri.py:5 | `::parse` không tồn tại — API thật: `graph`/`validate` | CẢ HAI (Beam: PARTIAL) | grep def: included/graph/replace/validate |
| 5 | scripts/deploy_niri_tree.py:5 | `::planning` sai tên — hàm thật là `plan` (deploy_niri.py:91) | **Beam** (GLM lúc đầu chấp nhận vì từ "planning" có trong prose) | máy thật: `def plan` dòng 91 ✓ |
| 6 | docs/WORKSPACE_MAP.md §1/§7/§9 | Anchor `check_architecture.py:152-155`/`:1-164` pin theo BASELINE; nhánh thật: file 170 dòng, khối size-ratchet 156-161, largeFiles 159-161 | CẢ HAI (Beam gọi "minor offset") | sed 156-161 xác nhận |

**Phân kỳ chất lượng (không tính lỗi):**
- scripts/backend_providers.py:6 `ActionRegistry.provide` — token ghép không grep -w được (Beam PARTIAL, GLM chấp nhận từng phần). Cosmetic.
- scripts/check.sh:3 — REL mơ hồ "tests/, migration gates" (GLM đánh dấu, Beam cho qua). Chất liệu tag, không sai quan hệ.

## 3. Trọng tài các phân kỳ
- **powerProfile (mục 3):** GLM đúng, Beam miss — xác nhận trên máy thật lẫn replica. Bài học: audit đơn đường vẫn bỏ sót; dual-audit có giá trị thực.
- **planning (mục 5):** Beam đúng, GLM ban đầu quá dễ dãi (word-match thay vì symbol-match). Nâng cấp thành lỗi.
- Còn lại: hai tuyến khác nhau ở mức nghiêm khắc tiêu chí, không khác nhau về sự thật.

## 4. Kết luận cuối
- **Tỷ lệ ảo giác thật sự: 5/108 thẻ REL (~4.6%)** — toàn bộ là *sai tên symbol / sai file đích*, KHÔNG có quan hệ bịa (đường dẫn 180/180 thật, quan hệ mô tả đều có thật, chỉ trỏ sai chỗ).
- **INVARIANT/GOTCHA: 0 ảo giác** (36/36 đúng, đối chiếu từng câu với code).
- **Map: đáng tin cậy** — mọi ref tồn tại + trong phạm vi; duy nhất 1 cụm anchor lệch dòng (mục 6) do pin theo baseline.
- **Không đổi hành vi: CHỨNG MINH** (hai đường độc lập: AST/string-aware stripper chạy lại từ đầu + inspect hunks của Beam).
- **Đề xuất:** 1 commit comment-only nhỏ sửa 5 thẻ REL (mục 1-5) + refresh anchor map (mục 6) trước khi merge — chưa làm, chờ bạn duyệt.

## 5. Chữ ký đường dẫn bằng chứng
- Replica patch: md5 `9ad76afc5ba63fc74e8b81084f79bea6` (byte-exact với máy thật)
- Beam Max session: `ses_e40ba3b11ffetYsL1bdSeobvHg` (outcome succeeded, model beam/ollama-cloud/max)
- Bridge worker session trọng phúc: `1e23f2bc-35b4-4fe6-9564-7d54e299271b`
- Báo cáo gốc: `route1_report.md` (GLM), `beam_report_max.md` (Beam Max), `beam_report_run1_iceman.md` (run phụ, model iceman-free — không dùng làm tuyến chính thức)
