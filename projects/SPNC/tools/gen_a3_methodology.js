// gen_a3_methodology.js — Chương 3 Methodology (bản nháp) cho khóa luận SPNC
// Nguồn dữ liệu: SOURCE_REGISTRY (S1-S6), ITEM_BANK (cấu trúc phiếu), OPEN_QUESTIONS (G1-G8), DECISION_LOG (D1-D8)
// Format: khuôn Bài 0/Bài 1 — bìa R5 + TOC La Mã + thân Ả Rập, TNR toàn bộ
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Footer, PageNumber, NumberFormat, AlignmentType, HeadingLevel,
  WidthType, BorderStyle, ShadingType, TableOfContents, SectionType,
  TableLayoutType,
} = require("docx");
const fs = require("fs");

const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };
const FONT = { ascii: "Times New Roman", eastAsia: "Times New Roman" };

// ── R5 cover (giống Bài 0/1) ──
function calcR5MetaLayout(metaEntries, fontPt = 12) {
  const maxLabelLen = Math.max(...metaEntries.map(e => [...e.label].length));
  const labelNeedTw = (maxLabelLen + 2) * fontPt * 20;
  const totalNeedTw = labelNeedTw + 5000;
  const tablePct = Math.min(75, Math.max(55, Math.ceil(totalNeedTw / 11906 * 100)));
  const rawLabelPct = Math.ceil(labelNeedTw / (tablePct / 100 * 11906) * 100);
  return { tablePct, labelPct: Math.max(25, Math.min(45, rawLabelPct)) };
}
function buildR5MetaTable(metaEntries) {
  const { tablePct, labelPct } = calcR5MetaLayout(metaEntries);
  const valuePct = 100 - labelPct;
  const bottomBorder = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
  const rows = metaEntries.map(entry => new TableRow({
    children: [
      new TableCell({
        width: { size: labelPct, type: WidthType.PERCENTAGE },
        borders: noBorders, margins: { top: 60, bottom: 60, left: 0, right: 0 },
        children: [new Paragraph({
          alignment: AlignmentType.LEFT, spacing: { before: 60, after: 60, line: 400 },
          children: [new TextRun({ text: entry.label + ":", size: 24, font: FONT })],
        })],
      }),
      new TableCell({
        width: { size: valuePct, type: WidthType.PERCENTAGE },
        borders: { top: NB, left: NB, right: NB, bottom: bottomBorder },
        margins: { top: 60, bottom: 60, left: 80, right: 0 },
        children: [new Paragraph({
          alignment: AlignmentType.LEFT, spacing: { before: 60, after: 60, line: 400 },
          children: [new TextRun({ text: entry.value, size: 24, font: FONT })],
        })],
      }),
    ],
  }));
  return new Table({
    width: { size: tablePct, type: WidthType.PERCENTAGE },
    alignment: AlignmentType.CENTER, layout: TableLayoutType.FIXED,
    borders: allNoBorders, rows,
  });
}
function buildCoverR5(config) {
  const PAGE_H = 16838;
  const simMarginLR = 1701, simMarginT = 1200;
  const titleLines = config.titleLines;
  const titlePt = config.titlePt;
  const metaEntries = (config.metaLines || []).map(line => {
    const idx = line.indexOf(":");
    return { label: line.slice(0, idx).trim(), value: line.slice(idx + 1).trim() };
  });
  const schoolNameH = 38 * 23 + 400;
  const titleTotalH = titleLines.length * (titlePt * 23 + 200);
  const subtitleH = 15 * 23 + 600;
  const metaTableH = metaEntries.length * 520;
  const fixedH = schoolNameH + titleTotalH + subtitleH + metaTableH + 3 * 350 + 12 * 23 + 200;
  const remaining = Math.max(15638 - fixedH, 600);
  const topSpacing = Math.min(Math.floor(remaining * 0.28) + simMarginT, 4200);
  const midSpacing = Math.min(Math.floor((remaining - simMarginT) * 0.18), 2000);
  const bottomSpacing = Math.max(remaining - topSpacing + simMarginT - midSpacing, 400);

  const children = [];
  children.push(new Paragraph({ spacing: { before: topSpacing } }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 400, line: 520, lineRule: "atLeast" },
    children: [new TextRun({ text: config.schoolName, size: 38, characterSpacing: 30, font: FONT })],
  }));
  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: i < titleLines.length - 1 ? 120 : 300, line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [new TextRun({ text: titleLines[i], size: titlePt * 2, bold: true, font: FONT })],
    }));
  }
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: config.subtitle, size: 30, font: FONT })],
  }));
  children.push(new Paragraph({ spacing: { before: midSpacing } }));
  if (metaEntries.length) children.push(buildR5MetaTable(metaEntries));
  children.push(new Paragraph({ spacing: { before: bottomSpacing } }));
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: config.footerRight, size: 24, color: "404040", font: FONT })],
  }));
  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE }, layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: PAGE_H, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: "FFFFFF" },
        borders: noBorders, verticalAlign: "top",
        margins: { left: simMarginLR, right: simMarginLR },
        children,
      })],
    })],
  })];
}

// ── body helpers ──
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160, line: 312 },
    children: [new TextRun({ text, bold: true, size: 32, color: "000000", font: FONT })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120, line: 312 },
    children: [new TextRun({ text, bold: true, size: 28, color: "000000", font: FONT })],
  });
}
function body(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, size: 24, color: "000000", font: FONT })];
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 480 },
    spacing: { line: 312, after: 80 },
    ...opts.para,
    children: runs,
  });
}
function note(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT, spacing: { line: 312, before: 60, after: 160 },
    children: [new TextRun({ text, size: 21, color: "5A5A00", italics: true, font: FONT })],
  });
}
function ph(text) { // placeholder run — nổi bật màu cam đậm
  return new TextRun({ text, size: 24, bold: true, color: "B45309", font: FONT });
}
function t(text) {
  return new TextRun({ text, size: 24, color: "000000", font: FONT });
}
function mkTable(header, rows, widths) {
  const mkCell = (content, isHeader, w) => new TableCell({
    width: { size: w, type: WidthType.PERCENTAGE },
    shading: isHeader ? { type: ShadingType.CLEAR, fill: "EFEFE8" } : undefined,
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    children: [new Paragraph({ spacing: { line: 300 },
      children: Array.isArray(content) ? content : [new TextRun({ text: content, bold: isHeader, size: 21, font: FONT })] })],
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: "9AA6B2" },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: "9AA6B2" },
      left: NB, right: NB,
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: "D0D0D0" },
      insideVertical: NB,
    },
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: header.map((c, i) => mkCell(c, true, widths[i])) }),
      ...rows.map(r => new TableRow({ cantSplit: true, children: r.map((c, i) => mkCell(c, false, widths[i])) })),
    ],
  });
}
function tableTitle(text) {
  return new Paragraph({
    keepNext: true, spacing: { before: 160, after: 60 },
    children: [new TextRun({ text, bold: true, size: 21, font: FONT })],
  });
}

const pgSize = { width: 11906, height: 16838 };
const pgMargin = { top: 1440, bottom: 1440, left: 1701, right: 1417 };
function pageNumFooter() {
  return new Footer({ children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, font: FONT })],
  })] });
}

// ══════════════ NỘI DUNG — CHƯƠNG 3 METHODOLOGY (NHÁP) ══════════════
const B = [];

// — 3.1 —
B.push(h1("3.1. Thiết kế nghiên cứu và các câu hỏi nghiên cứu"));
B.push(body([t("Nghiên cứu sử dụng "), t("thiết kế hỗn hợp giải thích (explanatory mixed-methods design)"), t(" với thành phần định lượng đi trước và thành phần định tính nối tiếp nhằm lý giải kết quả định lượng. Cách thiết kế này phù hợp vì đề tài cần trả lời cả câu hỏi mức độ (lo âu ở mức nào, yếu tố nào gặp nhiều nhất) lẫn câu hỏi cơ chế (vì sao những yếu tố đó gây lo âu cho sinh viên). Thành phần định lượng đo lường mức độ lo âu và tần suất từng nhóm yếu tố bằng phiếu khảo sát thang chuẩn; thành phần định tính đào sâu qua phỏng vấn bán cấu trúc với sinh viên có điểm lo âu cao và thấp để hiểu trải nghiệm đằng sau các con số.")]));
B.push(body([t("Ba câu hỏi nghiên cứu (RQ) đã được chốt ở giai đoạn thiết kế đề cương và giữ nguyên xuyên suốt. RQ1 hỏi mức độ lo âu phiên dịch đuổi của sinh viên năm ba ngành Ngôn ngữ Anh là bao nhiêu, đo bằng thang Dong-20 đã thích nghi; RQ2 hỏi nhóm yếu tố nào gây lo âu nhiều nhất theo nhận thức của sinh viên, đo bằng bộ item tự phát triển trên khung sáu nhóm của Ferdowsi và Razmi (2024); RQ3 hỏi vì sao những yếu tố đó gây lo âu, trả lời bằng phỏng vấn bán cấu trúc và phân tích chủ đề. Thứ tự này có chủ đích: biết "), t("bao nhiêu"), t(" trước, rồi "), t("cái gì"), t(", rồi mới "), t("vì sao"), t(" — mỗi bước dùng kết quả bước trước để định hướng bước sau.")]));
B.push(note("Ghi chú biên tập: các quyết định thiết kế ở chương này kế thừa biên bản quyết định D1–D8 của nhóm nghiên cứu; mọi thay đổi sau này phải được ghi lại và trình GVHD trước khi áp dụng."));

// — 3.2 —
B.push(h1("3.2. Participants và bối cảnh nghiên cứu (người tham gia)"));
B.push(body([t("Người tham gia là sinh viên năm ba ngành Ngôn ngữ Anh, Trường Đại học Sư phạm Thành phố Hồ Chí Minh (HCMUE), đã học hoặc đang học học phần phiên dịch đuổi. Tiêu chí chọn: (1) đang theo học năm ba khoa Tiếng Anh; (2) đã hoàn thành học phần phiên dịch đuổi "), ph("[tên học phần — chờ U2]"), t("; (3) đồng ý tham gia nghiên cứu có ký mẫu đồng thuận. Tiêu chí loại: sinh viên học lại chưa hoàn thành học phần hoặc vắng quá số buổi quy định.")]));
B.push(body([t("Cỡ mẫu dự kiến: khảo sát định lượng "), ph("n ≈ 80–120"), t(" (mục tiêu n≥100 để tương quan và so sánh nhóm đủ ổn định), trong đó pilot 25–30 người. Thành phần định tính: phỏng vấn 6–8 sinh viên chọn theo điểm Dong-20 (2 nhóm cao – thấp, mỗi nhóm 3–4 người, chọn tối đa khác biệt — maximum variation sampling) để đảm bảo quan điểm đa dạng. "), ph("[Sĩ số thực tế và số lớp — chờ U2]"), t(" sẽ được cập nhật khi có thông tin từ handbook khoa.")]));
B.push(tableTitle("Bảng 3.1. Tóm tắt kế hoạch người tham gia"));
B.push(mkTable(
  ["Thành phần", "Số lượng", "Cách chọn", "Vai trò trong nghiên cứu"],
  [
    ["Pilot (kiểm định công cụ)", "25–30", "Thuận tiện, khác nhóm khảo sát chính", "Tính Cronbach alpha, item-total; loại/sửa item yếu"],
    ["Khảo sát chính thức", "80–120", "Toàn bộ lớp đạt tiêu chí (thuận tiện)", "Trả lời RQ1, RQ2"],
    ["Phỏng vấn bán cấu trúc", "6–8", "Chọn theo điểm Dong-20 (cao/thấp)", "Trả lời RQ3"],
  ],
  [30, 14, 28, 28]));
B.push(note("Phương án chọn mẫu thuận tiện đã được chốt ở D3 vì khả thi trong thực tế lớp học; hạn chế của chọn mẫu thuận tiện sẽ được khai báo trong phần Limitations (chương 5)."));

// — 3.3 —
B.push(h1("3.3. Công cụ nghiên cứu"));
B.push(body([t("Bộ công cụ gồm ba phần trong một phiếu khảo sát song ngữ Anh–Việt. Quyết định dùng song ngữ (G2) vì sinh viên ngành Ngôn ngữ Anh thành thạo cả hai ngôn ngữ; bản song ngữ giúp người trả lời hiểu đúng nghĩa item và giảm sai lệch do dịch một chiều.")]));
B.push(h2("3.3.1. Part A — Thông tin nhân khẩu học"));
B.push(body([t("5–7 câu hỏi đóng: tuổi, giới tính, lớp, học kỳ đã học học phần phiên dịch đuổi, kinh nghiệm phiên dịch thực tế (nếu có). Dữ liệu này dùng để mô tả mẫu và làm biến số so sánh nhóm trong phân tích phụ (G6).")]));
B.push(h2("3.3.2. Part B — Thang Dong-20 đã thích nghi"));
B.push(body([t("Thang mức độ lo âu phiên dịch 20 item của Dong, Chen và Yu (2013), thang Likert 5 điểm (1 = Hoàn toàn không đúng với tôi … 5 = Hoàn toàn đúng với tôi), ba chiều: Độ nặng nề nhiệm vụ (6 item), Tính phục vụ (7 item), và Tự tin chung (7 item). Item 1–8 diễn đạt theo hướng tích cực nên "), t("phải đảo điểm khi tính (điểm mới = 6 − điểm gốc)"), t("; tổng điểm 20–100, điểm càng cao lo âu càng nhiều. Độ tin cậy gốc: Cronbach alpha .92 (n=245); pilot .91 (n=25); test–retest .84 (n=60). Đây là lý do chọn thang này cho RQ1: đã có hệ số độ tin cậy công bố từ nguồn gốc.")]));
B.push(body([t("Hai điều chỉnh thích nghi đã chốt: item 2 đổi bối cảnh \u201ctrên đường đến lớp\u201d cho khớp môi trường HCMUE; item 10 (bối cảnh hành nghề) chuyển thành tình huống role-play trong lớp học (G5) vì sinh viên năm ba chưa làm phiên dịch chuyên nghiệp — việc bỏ hẳn item sẽ làm lệch cấu trúc thang gốc. "), ph("[Trạng thái xin phép GS. Dong Yanping — thư soạn xong, chờ duyệt và gửi; chờ U5]"), t(" Việc dịch song ngữ tuân theo quy trình dịch xuôi–ngược độc lập (xem 3.4).")]));
B.push(h2("3.3.3. Part C — Bộ 30 item tự phát triển"));
B.push(body([t("Bộ 30 item (6 nhóm × 5 item) tự phát triển trên khung sáu nhóm yếu tố của Ferdowsi và Razmi (2024): lo âu cá nhân, đầu vào, kỹ năng ghi chú, môi trường, đầu ra, và giáo viên. Mỗi item gắn nhãn nguồn rõ ràng trong tài liệu nội bộ: 5 item nguyên văn từ Tran (2025), 3 phỏng theo Dong và cộng sự (2013), 2 phỏng theo FLCAS của Horwitz, Horwitz và Cope (1986), 1 câu chủ đề thảo luận từ Tran (2025), và 19 item tự viết từ các tiểu khía cạnh (sub-facet) của khung Ferdowsi và Razmi. Bộ này được gọi đúng danh xưng là "), t("researcher-developed, pending pilot validation"), t(" (tự phát triển, chờ kiểm định bằng pilot) — không gọi là thang chuẩn hóa, vì chưa qua kiểm định đầy đủ.")]));
B.push(tableTitle("Bảng 3.2. Cấu trúc bộ 30 item theo nhóm yếu tố và nhãn nguồn"));
B.push(mkTable(
  ["Nhóm yếu tố (F&R 2024)", "Số item", "Nguồn item (nhãn nội bộ)"],
  [
    ["Lo âu cá nhân (individual)", "5", "Tự viết từ sub-facet: general anxious feelings, low concentration, perfectionism, introversion"],
    ["Đầu vào (input)", "5", "Tự viết: ngôn ngữ nguồn + người nói"],
    ["Kỹ năng ghi chú (note-taking)", "5", "Tự viết: kỹ năng + sự sáng tạo"],
    ["Môi trường (environmental)", "5", "Tự viết: tiếng ồn + sự hiện diện của bạn học"],
    ["Đầu ra (output)", "5", "Tự viết: truyền đạt ý nghĩa + phần trình bày"],
    ["Giáo viên (teacher)", "5", "Tự viết: kiểm tra/chấm điểm + hành vi ứng xử"],
  ],
  [34, 12, 54]));
B.push(body([t("Trong 30 item có 5 item nguyên văn của Tran (2025) — nguồn duy nhất công bố item nguyên văn trong bối cảnh Việt Nam (63 sinh viên Thái Nguyên, Anh–Việt) — và 1 câu hỏi mở về chủ đề thảo luận. "), ph("[Bảng 30 item song ngữ đầy đủ — chờ bản nháp cũ của người dùng (U1); không tái tạo từ trí nhớ theo luật D5]")]));

// — 3.4 —
B.push(h1("3.4. Quy trình kiểm định công cụ"));
B.push(body([t("Bộ công cụ qua năm bước trước khi khảo sát chính thức. Bước 1 — dịch xuôi–ngược: hai người dịch độc lập dịch item tiếng Anh sang tiếng Việt và ngược lại, đối chiếu sai khác, hợp nhất thành bản cuối. Bước 2 — duyệt nội dung (content validity): hai đến ba chuyên gia phiên dịch và phương pháp nghiên cứu duyệt từng item theo tiêu chí rõ nghĩa, không nhập nhằng, khớp tiểu khía cạnh. Bước 3 — phỏng vấn nhận thức (cognitive interview): 3–5 sinh viên đọc to suy nghĩ khi trả lời để phát hiện item khó hiểu; sửa lại chữ nghĩa nhưng không đổi ý. Bước 4 — pilot 25–30 sinh viên: tính Cronbach alpha từng chiều của Dong-20 và tổng bộ 30; item có tương quan item-total dưới .30 được xem xét loại hoặc sửa. Bước 5 — hoàn thiện bộ công cụ dựa trên kết quả pilot, trình GVHD duyệt trước khi in.")]));
B.push(body([t("Về EFA (phân tích nhân tố khám phá): nhóm quyết định KHÔNG chạy EFA (D4). Với n≈100, EFA không ổn định về mặt thống kê (quy tắc thông thường cần tối thiểu 5–10 người/item, tức 150–300 cho bộ 30 item); bộ 30 item đã có khung lý thuyết sáu nhóm từ trước nên chỉ cần kiểm định độ tin cậy nội bộ bằng alpha, không cần khám phá cấu trúc. Quyết định này sẽ được viết lại trong phần Limitations nếu người chấm hỏi.")]));
B.push(note("Toàn bộ quy trình 5 bước và lý do không chạy EFA kế thừa quyết định D4 và G7 (phương án A: dừng ở pilot, chuẩn khóa luận)."));

// — 3.5 —
B.push(h1("3.5. Thu thập dữ liệu"));
B.push(body([t("Khảo sát định lượng: phát phiếu giấy hoặc Google Forms sau giờ học phần, thời gian trả lời 15–20 phút; nghiên cứu giải thích mục đích, quyền từ chối và ẩn danh trước khi phát. Phỏng vấn bán cấu trúc: 30–45 phút mỗi buổi, ghi âm với sự đồng ý, tại phòng học trống; câu hỏi mở theo khung sáu nhóm, ví dụ: \u201cKể về một lần em thấy lo âu nhất trong giờ phiên dịch đuổi — chuyện gì xảy ra, điều gì làm em căng thẳng?\u201d. Dữ liệu phỏng vấn được chuyển ngữ verbatim trong vòng 48 giờ sau mỗi buổi.")]));
B.push(body([ph("[Timeline chi tiết 16 tuần — chờ U2 (học kỳ) để gắn mốc; khung G8: proposal → công cụ → pilot → thu dữ liệu → phân tích → viết → chấm]")]));

// — 3.6 —
B.push(h1("3.6. Phân tích dữ liệu"));
B.push(tableTitle("Bảng 3.3. Kế hoạch phân tích theo câu hỏi nghiên cứu"));
B.push(mkTable(
  ["RQ", "Dữ liệu", "Phép phân tích", "Công cụ"],
  [
    ["RQ1 — Mức độ lo âu", "Dong-20 (20 item, đảo 1–8)", "Thống kê mô tả: M, SD theo chiều và tổng; so với điểm trung bình thang (60/100)", "SPSS / JASP"],
    ["RQ2 — Nhóm yếu tố nhiều nhất", "Bộ 30 item (6 nhóm × 5)", "Mean từng nhóm, xếp hạng; kiểm định so sánh mean giữa 6 nhóm (ANOVA một chiều lặp lại hoặc Friedman nếu phi chuẩn)", "SPSS / JASP"],
    ["RQ3 — Vì sao", "Phỏng vấn 6–8 buổi", "Phân tích chủ đề Braun và Clarke (2006) 6 bước; 2 người mã hóa độc lập, so chấm độ tin cậy", "Bằng tay + bảng tính"],
  ],
  [24, 22, 34, 20]));
B.push(body([t("Với RQ3, quy trình sáu bước của Braun và Clarke (2006) được áp dụng đầy đủ: làm quen dữ liệu → mã hóa ban đầu → tìm chủ đề → xem lại chủ đề → định nghĩa và đặt tên chủ đề → viết báo cáo. Hai người mã hóa độc lập mã 20% trích dẫn trùng nhau và tính độ đồng thuận; khác biệt được giải quyết bằng thảo luận. Phân tích phụ nếu n≥100 (G6): tương quan Dong-20 với tổng bộ 30, so sánh theo giới tính và lớp bằng t-test hoặc ANOVA.")]));
B.push(body([t("Tiêu chuẩn ý nghĩa thống kê alpha = .05; kích thước hiệu ứng báo cáo kèm (eta bình phương cho ANOVA, r cho tương quan) vì với n≈100 giá trị p dễ đạt ý nghĩa với hiệu ứng nhỏ — kích thước hiệu ứng cho biết mức đáng kể thực tế. Dữ liệu thiếu: item thiếu quá 20% của một phần → loại phiếu của phần đó; điền khuyết không dùng vì phiếu ngắn và tỷ lệ thiếu dự kiến thấp.")]));

// — 3.7 —
B.push(h1("3.7. Đạo đức nghiên cứu"));
B.push(body([t("Nghiên cứu tuân thủ quy định đạo đức nghiên cứu của HCMUE: (1) xin phép giám học phần và khoa trước khi thu dữ liệu; (2) người tham gia ký mẫu đồng thuận nêu rõ mục đích, quyền rút lui bất cứ lúc nào không bị ảnh hưởng điểm số; (3) dữ liệu ẩn danh hóa — không thu tên, mã sinh viên; (4) dữ liệu thô lưu trữ an toàn, chỉ nhóm nghiên cứu được tiếp cận, hủy sau khi khóa luận hoàn thành theo quy định; (5) kết quả chỉ báo cáo dạng tổng hợp, không trích danh tính. Mẫu đồng thuận và thư xin phép đã soạn sẵn trong bộ hồ sơ nghiên cứu.")]));

// — 3.8 —
B.push(h1("3.8. Vị thế của nhà nghiên cứu và giới hạn thiết kế"));
B.push(body([t("Người nghiên cứu là sinh viên ngành Ngôn ngữ Anh đã trải qua học phần phiên dịch đuổi — vị thế người trong cuộc giúp hiểu trải nghiệm nhưng cần được khai báo để người đọc đánh giá độ khách quan. Giới hạn thiết kế đã biết và sẽ khai báo trong chương 5: chọn mẫu thuận tiện (không khái quát hóa ra ngoài khoa Tiếng Anh HCMUE); tự báo cáo (self-report) có thể thiên lệch mong muốn xã hội; thiết kế cắt ngang (một thời điểm) không nói được quan hệ nhân quả; bộ 30 item chưa chuẩn hóa (chỉ dừng pilot — G7).")]));

// ══════════════ LẮP ══════════════
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: 24, color: "000000" }, paragraph: { spacing: { line: 312 } } },
      heading1: { run: { font: FONT, size: 32, bold: true, color: "000000" }, paragraph: { spacing: { before: 360, after: 160, line: 312 } } },
      heading2: { run: { font: FONT, size: 28, bold: true, color: "000000" }, paragraph: { spacing: { before: 240, after: 120, line: 312 } } },
    },
  },
  sections: [
    {
      properties: { page: { size: pgSize, margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCoverR5({
        schoolName: "KHÓA LUẬN TỐT NGHIỆP — BẢN NHÁP NỘI BỘ",
        titleLines: ["Chương 3. Phương pháp", "nghiên cứu (Methodology)"],
        titlePt: 30,
        subtitle: "Yếu tố gây lo âu trong phiên dịch đuổi ở sinh viên năm ba ngành Ngôn ngữ Anh, HCMUE",
        metaLines: [
          "Trạng thái: Bản nháp chờ U1 U2 (đánh dấu màu cam)",
          "Người soạn: Trợ lý nghiên cứu A3",
          "Ngày: 17 tháng 11 năm 2026",
          "Kế thừa: D1–D8, G1–G8, SOURCE_REGISTRY S1–S6",
        ],
        footerRight: "Mọi placeholder màu cam cần dữ liệu thật trước khi nộp",
      }),
    },
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN } },
      },
      footers: { default: pageNumFooter() },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 480, after: 360 },
          children: [new TextRun({ text: "MỤC LỤC", bold: true, size: 32, font: FONT })],
        }),
        new TableOfContents("Muc luc", { hyperlink: true, headingStyleRange: "1-2" }),
        new Paragraph({
          spacing: { before: 200 },
          children: [new TextRun({
            text: "Ghi chú: Mục lục tạo bằng trường tự động. Sau khi chỉnh sửa tài liệu, hãy nhấp chuột phải vào mục lục rồi chọn Update Field để cập nhật số trang chính xác.",
            italics: true, size: 18, color: "888888", font: FONT })],
        }),
      ],
    },
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } },
      },
      footers: { default: pageNumFooter() },
      children: B,
    },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/home/z/my-project/download/Chuong3_Methodology_nhap.docx", buf);
  console.log("OK: Chuong3_Methodology_nhap.docx", buf.length, "bytes");
});
