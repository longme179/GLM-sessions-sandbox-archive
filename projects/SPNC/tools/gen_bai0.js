// gen_bai0.js — Sổ tay học tập Bài 0 (tiếng Việt) cho đề tài lo âu phiên dịch đuổi HCMUE
// Kiến trúc: Section 1 bìa R5 (không số trang) → Section 2 mục lục (La Mã) → Section 3 thân bài (Ả Rập, start=1)
// Font tiếng Việt: Times New Roman cho cả ascii + eastAsia (tiếng Việt dùng Latin mở rộng, TNR phủ đủ)
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  PageBreak, Footer, PageNumber, NumberFormat, AlignmentType, HeadingLevel,
  WidthType, BorderStyle, ShadingType, TableOfContents, SectionType,
  TableLayoutType,
} = require("docx");
const fs = require("fs");

// ── Borders helpers (bắt buộc cho mọi bảng bìa) ──
const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };

// ── estimateTextWidth (mixed CJK/Latin) từ design-system.md ──
// Latin factor nâng lên pt*13 (thay vì pt*11) để chừa dư cho chữ Việt có dấu + đậm
// (bài học 2026-11-17: pt*11 làm tiêu đề tràn, LibreOffice tự wrap xấu "gì" xuống dòng riêng)
function estimateTextWidth(text, pt) {
  let width = 0;
  for (const ch of text) {
    const code = ch.codePointAt(0);
    const isCJK = (code >= 0x4E00 && code <= 0x9FFF) || (code >= 0x3400 && code <= 0x4DBF) ||
      (code >= 0x3000 && code <= 0x303F) || (code >= 0xFF00 && code <= 0xFFEF) ||
      (code >= 0x2E80 && code <= 0x2EFF);
    width += isCJK ? pt * 20 : pt * 13;
  }
  return width;
}

// ── calcTitleLayoutMixed: R5 dùng ước lượng độ rộng thay vì đếm ký tự ──
function calcTitleLayoutMixed(title, maxWidthTwips, preferredPt = 36, minPt = 24) {
  let titlePt = preferredPt;
  let lines;
  const splitByWidth = (pt) => {
    const words = title.split(/\s+/);
    const lines = [];
    let cur = "";
    for (const w of words) {
      const cand = cur ? cur + " " + w : w;
      if (estimateTextWidth(cand, pt) <= maxWidthTwips) cur = cand;
      else { if (cur) lines.push(cur); cur = w; }
    }
    if (cur) lines.push(cur);
    return lines;
  };
  while (titlePt >= minPt) {
    lines = splitByWidth(titlePt);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) { lines = splitByWidth(minPt); titlePt = minPt; }
  // gộp dòng mồ côi (≤2 ký tự)
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop();
    lines[lines.length - 1] += " " + last;
  }
  return { titlePt, titleLines: lines };
}

// ── R5 meta table (giữ nguyên công thức design-system.md) ──
function calcR5MetaLayout(metaEntries, fontPt = 12) {
  const maxLabelLen = Math.max(...metaEntries.map(e => [...e.label].length));
  const labelNeedTw = (maxLabelLen + 2) * fontPt * 20;
  const valueNeedTw = 5000;
  const totalNeedTw = labelNeedTw + valueNeedTw;
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
        borders: noBorders,
        margins: { top: 60, bottom: 60, left: 0, right: 0 },
        children: [new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { before: 60, after: 60, line: 400 },
          children: [new TextRun({
            text: entry.label + ":",
            size: 24, font: { eastAsia: "Times New Roman", ascii: "Times New Roman" },
          })],
        })],
      }),
      new TableCell({
        width: { size: valuePct, type: WidthType.PERCENTAGE },
        borders: { top: NB, left: NB, right: NB, bottom: bottomBorder },
        margins: { top: 60, bottom: 60, left: 80, right: 0 },
        children: [new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { before: 60, after: 60, line: 400 },
          children: [new TextRun({
            text: entry.value,
            size: 24, font: { eastAsia: "Times New Roman", ascii: "Times New Roman" },
          })],
        })],
      }),
    ],
  }));
  return new Table({
    width: { size: tablePct, type: WidthType.PERCENTAGE },
    alignment: AlignmentType.CENTER,
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows,
  });
}

// ── buildCoverR5 (theo design-system.md, mục 1655–1652) ──
function buildCoverR5(config) {
  const PAGE_H = 16838, SAFETY = 1200;
  const safeH = PAGE_H - SAFETY;
  const simMarginLR = 1701, simMarginT = 1200;
  const contentW = 11906 - simMarginLR * 2;

  // Tiêu đề ngắn, tự ngắt tại ranh giới ngữ nghĩa (2 dòng cân) — không tin auto-wrap
  const titleLines = ["Bài 0: Đề tài hỏi gì", "và đo bằng cách nào"];
  const titlePt = 33;
  const titleSize = titlePt * 2;

  const metaEntries = (config.metaLines || []).map(line => {
    const sep = line.indexOf("：") !== -1 ? "：" : ":";
    const idx = line.indexOf(sep);
    if (idx === -1) return { label: line, value: "" };
    return { label: line.slice(0, idx).trim(), value: line.slice(idx + sep.length).trim() };
  });

  const schoolNameH = config.schoolName ? (22 * 23 + 400) : 0;
  const titleTotalH = titleLines.length * (titlePt * 23 + 200);
  const subtitleH = config.subtitle ? (15 * 23 + 600) : 0;
  const metaRowH = 520;
  const metaTableH = metaEntries.length * metaRowH;
  const footerH = config.footerRight ? (12 * 23 + 200) : 0;
  const spacerParas = 3 * 350;
  const fixedH = schoolNameH + titleTotalH + subtitleH + metaTableH + footerH + spacerParas;
  const remaining = Math.max(safeH - fixedH, 600);

  const topSpacing = Math.min(Math.floor(remaining * 0.28) + simMarginT, 4200);
  const midSpacing = Math.min(Math.floor((remaining - simMarginT) * 0.18), 2000);
  const bottomSpacing = Math.min(remaining - topSpacing + simMarginT - midSpacing, 5500);

  const children = [];
  children.push(new Paragraph({ spacing: { before: topSpacing } }));

  if (config.schoolName) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 400, line: 520, lineRule: "atLeast" },
      children: [new TextRun({ text: config.schoolName, size: 38, characterSpacing: 30,
        font: { eastAsia: "Times New Roman", ascii: "Times New Roman" } })],
    }));
  }

  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: i < titleLines.length - 1 ? 120 : 300, line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [new TextRun({ text: titleLines[i], size: titleSize, bold: true,
        font: { eastAsia: "Times New Roman", ascii: "Times New Roman" } })],
    }));
  }

  if (config.subtitle) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: config.subtitle, size: 30,
        font: { eastAsia: "Times New Roman", ascii: "Times New Roman" } })],
    }));
  }

  children.push(new Paragraph({ spacing: { before: midSpacing } }));
  if (metaEntries.length > 0) children.push(buildR5MetaTable(metaEntries));
  children.push(new Paragraph({ spacing: { before: bottomSpacing } }));

  if (config.footerRight) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: config.footerRight, size: 24, color: "404040",
        font: { eastAsia: "Times New Roman", ascii: "Times New Roman" } })],
    }));
  }

  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
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

// ── Body helpers (Profile A: đen thuần, TNR, 1.3x, thụt đầu dòng 480) ──
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160, line: 312 },
    children: [new TextRun({ text, bold: true, size: 32, color: "000000",
      font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120, line: 312 },
    children: [new TextRun({ text, bold: true, size: 28, color: "000000",
      font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
  });
}
function body(text, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: 480 },
    spacing: { line: 312, after: 80 },
    children: [new TextRun({ text, size: 24, color: "000000", bold: !!opts.bold,
      font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
  });
}
// đoạn không thụt đầu dòng (chú thích, ghi chú dưới bảng)
function note(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { line: 312, before: 60, after: 160 },
    children: [new TextRun({ text, size: 21, color: "404040", italics: true,
      font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
  });
}
// ô "câu hỏi tự kiểm tra"
function quizBox(qs) {
  const border = { style: BorderStyle.SINGLE, size: 4, color: "555555" };
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { top: border, bottom: border, left: border, right: border, insideHorizontal: NB, insideVertical: NB },
    rows: [new TableRow({
      cantSplit: false,
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: "F5F5F0" },
        margins: { top: 120, bottom: 120, left: 200, right: 200 },
        width: { size: 100, type: WidthType.PERCENTAGE },
        children: [
          new Paragraph({
            spacing: { line: 312, after: 60 },
            children: [new TextRun({ text: "Tự kiểm tra", bold: true, size: 24,
              font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
          }),
          ...qs.map((q, i) => new Paragraph({
            spacing: { line: 312, after: 40 },
            children: [new TextRun({ text: (i + 1) + ". " + q, size: 24,
              font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
          })),
        ],
      })],
    })],
  });
}
// bảng 2 cột RQ (tiêu đề giữ với bảng)
function rqTable(rows) {
  const header = ["Câu hỏi nghiên cứu", "Công cụ trả lời", "Kết quả ra là gì"];
  const widths = [30, 35, 35];
  const mkCell = (text, isHeader, w) => new TableCell({
    width: { size: w, type: WidthType.PERCENTAGE },
    shading: isHeader ? { type: ShadingType.CLEAR, fill: "EFEFE8" } : undefined,
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    children: [new Paragraph({
      spacing: { line: 312 },
      children: [new TextRun({ text, bold: isHeader, size: 21,
        font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
    })],
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
      new TableRow({ tableHeader: true, cantSplit: true, children: header.map((t, i) => mkCell(t, true, widths[i])) }),
      ...rows.map(r => new TableRow({ cantSplit: true, children: r.map((t, i) => mkCell(t, false, widths[i])) })),
    ],
  });
}

const pgSize = { width: 11906, height: 16838 };
const pgMargin = { top: 1440, bottom: 1440, left: 1701, right: 1417 };

function pageNumFooter() {
  return new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18,
        font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
    })],
  });
}

// ══════════════ NỘI DUNG THÂN BÀI ══════════════
const bodyChildren = [];

// ── Mở đầu: đọc tài liệu này thế nào ──
bodyChildren.push(h1("Lời mở đầu: đọc tài liệu này như thế nào"));
bodyChildren.push(body("Chào bạn. Đây là Bài 0 trong bộ Sổ tay học tập đi cùng đề tài khóa luận của bạn: nghiên cứu các yếu tố gây lo âu trong hoạt động phiên dịch đuổi (consecutive interpreting) ở sinh viên năm ba ngành Ngôn ngữ Anh, Trường Đại học Sư phạm Thành phố Hồ Chí Minh (HCMUE). Bộ sổ tay này viết cho người chưa từng học về phương pháp nghiên cứu: không có thuật ngữ nào xuất hiện mà không được giải thích ngay, và mọi khái niệm đều kèm một ví dụ bằng số cụ thể, đời thường."));
bodyChildren.push(body("Cách dùng: đọc theo thứ tự các mục, làm phần tự kiểm tra ở cuối mỗi phần (trả lời bằng miệng hoặc ghi ra giấy), rồi mới sang mục sau. Nếu trả lời sai, hãy đọc lại phần vừa học; nếu vẫn thấy khó, hãy nói với trợ lý nghiên cứu (chính là phần mềm trợ giúp bạn làm đề tài này) — nó sẽ giải thích lại theo cách khác. Mỗi bài sau sẽ dựa trên bài trước, giống như học bảng cửu chương trước khi học phép chia."));
bodyChildren.push(body("Bài 0 trả lời ba câu hỏi nền tảng: (1) Đề tài này hỏi cái gì? (2) Vì sao hỏi theo thứ tự đó? (3) Người ta đo một thứ vô hình như nỗi lo âu bằng cách nào? Hết Bài 0, bạn sẽ đọc được đề cương nghiên cứu (bản kế hoạch của khóa luận) và hiểu nó nói gì — dù chưa cần biết viết."));

// ── 1. Đề tài hỏi cái gì ──
bodyChildren.push(h1("1. Đề tài này hỏi cái gì"));
bodyChildren.push(body("Tên đầy đủ của đề tài là: An Investigation into Anxiety-Provoking Factors in Consecutive Interpreting among HCMUE Third-Year English Language Students (Điều tra các yếu tố gây lo âu trong phiên dịch đuổi ở sinh viên năm ba ngành Ngôn ngữ Anh, HCMUE). Nghe dài, nhưng khi tách ra thì chỉ có ba từ khóa cần hiểu."));
bodyChildren.push(body("Từ khóa thứ nhất: phiên dịch đuổi. Đây là kiểu phiên dịch mà người nói nói một đoạn ngắn rồi dừng lại, và người phiên dịch dịch lại toàn bộ đoạn đó cho người nghe. Ví dụ: giảng viên nói ba câu tiếng Anh, dừng, rồi một sinh viên dịch ba câu đó sang tiếng Việt cho cả lớp. Nó khác kiểu phiên dịch đồng thời (simultaneous interpreting) — nghe và dịch cùng lúc như phiên dịch trong cabin hội nghị. Trong lớp học ở HCMUE, sinh viên chủ yếu luyện kiểu đuổi."));
bodyChildren.push(body("Từ khóa thứ hai: lo âu. Ở đây không nói về lo âu bệnh lý (cần bác sĩ trị), mà là lo âu tình huống: cảm giác căng thẳng xuất hiện gắn với một tình huống cụ thể rồi tan đi. Ví dụ đời thường: bạn bình thản tán gẫu ngoài hành lang, nhưng bị gọi lên bảng dịch thì tim đập nhanh, tay lạnh, quên từ vừa học hôm qua — đó là lo âu tình huống. Nghiên cứu này chỉ quan tâm đến loại gắn với việc phiên dịch."));
bodyChildren.push(body("Từ khóa thứ ba: yếu tố gây lo âu, tức những thứ cụ thể bên trong tình huống khiến người ta lo âu. Ví dụ: người nói nói quá nhanh; sợ bạn cùng lớp cười khi mình dịch sai; ghi chú chưa kịp; từ vựng chuyên ngành lạ. Đề tài sẽ liệt kê khoảng 30 yếu tố như vậy, gom thành 6 nhóm, và hỏi: nhóm nào khiến sinh viên HCMUE lo âu nhất?"));

// ── 2. Ba câu hỏi nghiên cứu ──
bodyChildren.push(h1("2. Ba câu hỏi nghiên cứu: bao nhiêu, cái gì, tại sao"));
bodyChildren.push(body("Một nghiên cứu không tiến hành một cách tùy hứng; nó trả lời các câu hỏi nghiên cứu (research question, viết tắt RQ) — những câu hỏi cụ thể mà đề tài cam kết trả lời bằng dữ liệu thu được. Đề tài này có ba RQ, sắp xếp theo trình tự rất có chủ đích: mô tả trước, xếp hạng sau, giải thích cuối."));

bodyChildren.push(h2("2.1. RQ1 — Bao nhiêu: mức độ lo âu là gì?"));
bodyChildren.push(body("Câu hỏi 1 hỏi: sinh viên năm ba HCMUE lo âu ở mức độ nào khi phiên dịch đuổi? Nói cách khác: con số là bao nhiêu. Câu này được trả lời bằng thang đo Dong-20 (một bộ 20 câu hỏi do giáo sư Dong Yanping và cộng sự dựng năm 2013 để đo mức lo âu phiên dịch, sẽ học kỹ ở Bài 2). Mỗi sinh viên trả lời xong sẽ có một điểm tổng từ 20 đến 100; lấy trung bình (mean — tổng điểm mọi người chia cho số người) của cả mẫu, ta có mức độ lo âu trung bình của lớp."));
bodyChildren.push(body("Ví dụ bằng số: nếu khảo sát 100 sinh viên và điểm trung bình là 62, còn khoảng giá trị của thang là 20 đến 100, thì điểm 62 nằm ở vùng khá cao (giữa thang là 60). Con số này tự nó chưa nói nhóm yếu tố nào đáng sợ nhất — nó chỉ trả lời: nhìn chung, lo âu bao nhiêu? Đó là việc của RQ1."));

bodyChildren.push(h2("2.2. RQ2 — Cái gì: yếu tố nào lớn nhất?"));
bodyChildren.push(body("Câu hỏi 2 hỏi: trong 6 nhóm yếu tố gây lo âu, nhóm nào được sinh viên chấm là gây lo âu nhất, nhì, ba...? Đây là câu xếp hạng. Nó được trả lời bằng bộ 30 câu hỏi (6 nhóm, mỗi nhóm 5 câu) mà các phiên trước của đề tài đã soạn. Mỗi câu sinh viên chấm từ 1 (hoàn toàn không lo) đến 5 (lo âu rất nhiều); điểm trung bình của mỗi nhóm được tính rồi so sánh giữa các nhóm."));
bodyChildren.push(body("Ví dụ bằng số: nhóm Yếu tố đầu vào (input — thứ sinh viên phải tiếp nhận, như tốc độ người nói, giọng lạ, từ vựng khó) có thể được trung bình 4,1 điểm, còn nhóm Môi trường (environmental — ồn ào, sợ bị so sánh với bạn) được 3,2 điểm. Lúc đó ta tạm kết luận: sinh viên lo yếu tố đầu vào hơn yếu tố môi trường. Vì sao chỉ là tạm? Vì khoảng cách 4,1 với 3,2 có thật hay chỉ là nhiễu ngẫu nhiên — việc đó sẽ kiểm định bằng thống kê, học ở Bài 4."));

bodyChildren.push(h2("2.3. RQ3 — Tại sao: đằng sau con số là gì?"));
bodyChildren.push(body("Câu hỏi 3 hỏi: vì sao lại như vậy? Con số cho biết việc gì xảy ra nhưng không cho biết lý do. Để hiểu lý do, đề tài phỏng vấn sâu 10 đến 12 sinh viên được chọn từ ba mức lo âu: cao, trung bình, thấp (mỗi mức chừng 4 người). Chọn đủ ba mức vì lý do của người lo âu nhiều có thể khác lý do của người ít lo âu — nếu chỉ hỏi người lo âu cao, ta chỉ hiểu được một nửa bức tranh."));
bodyChildren.push(body("Ví dụ bằng số: khảo sát cho biết nhóm yếu tố giảng viên đứng hạng cao với 3,9 điểm. Phỏng vấn mới lộ chi tiết: có sinh viên nói thầy cô sửa lỗi ngay khi mình đang dịch khiến mình mất trí nhớ tạm thời; sinh viên khác lại nói chính việc thầy cô im lặng ghi giấy mới đáng sợ vì không biết mình sai ở đâu. Hai lý do khác nhau dẫn tới cùng một con số 3,9 — chỉ phỏng vấn mới tách được."));

bodyChildren.push(new Paragraph({
  keepNext: true,
  spacing: { before: 160, after: 60 },
  children: [new TextRun({ text: "Bảng 1. Ba câu hỏi nghiên cứu tóm tắt", bold: true, size: 21,
    font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
}));
bodyChildren.push(rqTable([
  ["RQ1. Mức độ lo âu là bao nhiêu?", "Thang Dong-20 (20 câu, bản đã thích nghi)", "Một con số điểm trung bình (ví dụ 62/100)"],
  ["RQ2. Nhóm yếu tố nào gây lo âu nhất?", "Bộ 30 câu hỏi tự phát triển (6 nhóm x 5 câu)", "Bảng xếp hạng 6 nhóm theo điểm trung bình"],
  ["RQ3. Vì sao lại như vậy?", "Phỏng vấn sâu 10-12 sinh viên (cao/trung bình/thấp)", "Các chủ đề giải thích đằng sau con số"],
]));
bodyChildren.push(note("Chú ý cột giữa: mỗi câu hỏi đi với một công cụ đo riêng. Sự khớp nhau giữa câu hỏi và công cụ là tiêu chí đầu tiên để hội đồng chấm đề cương tốt hay dở."));

bodyChildren.push(h2("2.4. Vì sao xếp theo thứ tự: bao nhiêu, cái gì, tại sao"));
bodyChildren.push(body("Thứ tự ba câu hỏi không ngẫu nhiên mà đi từ dễ đo đến khó đo, từ mô tả đến giải thích. RQ1 phải đi đầu vì nếu không biết mức độ lo âu bao nhiêu thì việc xếp hạng yếu tố (RQ2) thiếu điểm quy chiếu: nhóm yếu tố được 4,1 điểm nhưng tự thân mức lo âu chung chỉ 2,5 thì đó là mâu thuẫn cần kiểm tra dữ liệu. RQ2 đến trước RQ3 vì phỏng vấn (RQ3) cần biết trước nhóm yếu tố nào nổi bật để hỏi sâu đúng chỗ; nếu phỏng vấn trước thì không biết phải đào vào đâu."));
bodyChildren.push(body("Thứ tự này cũng chính là kiểu thiết kế gọi là hỗn hợp giải thích tuần tự (explanatory sequential mixed methods): làm phần định lượng trước (khảo sát số), rồi phần định tính sau (phỏng vấn) để giải thích cho con số. Từ định lượng (quantitative) nghĩa là đo bằng số; định tính (qualitative) nghĩa là hiểu bằng lời kể. Hai phần kết hợp vì mỗi thứ bù khuyết điểm của thứ kia: số cho biết việc gì xảy ra ở quy mô lớn nhưng câm lặng về lý do; lời kể sâu sắc về lý do nhưng chỉ từ vài người, không đại diện cho cả khóa."));
bodyChildren.push(body("Một cách hình dung: RQ1 là nhiệt kế (đo bao nhiêu độ), RQ2 là bản đồ (chỉ vùng nào nóng nhất), RQ3 là phóng viên điều tra (đến tận nơi hỏi vì sao nóng). Cả ba ghép lại thành một câu chuyện hoàn chỉnh — và đó cũng là trật tự các chương sẽ xuất hiện trong bản khóa luận cuối cùng."));

// ── 3. Khung 6 nhóm yếu tố ──
bodyChildren.push(h1("3. Sáu nhóm yếu tố: bản đồ của đề tài"));
bodyChildren.push(body("Ở RQ2, khoảng 30 yếu tố lo âu được gom thành 6 nhóm theo khung của nghiên cứu Ferdowsi và Razmi (2024). Gom nhóm giúp việc xếp hạng gọn gàng: thay vì so 30 dòng rời rạc, ta so 6 nhóm. Dưới đây là bản đồ 6 nhóm kèm ví dụ một yếu tố tiêu biểu trong mỗi nhóm; chi tiết đầy đủ 30 yếu tố nằm ở phiếu khảo sát và sẽ học ở Bài 3."));
bodyChildren.push(rqTable([
  ["Nhóm 1. Cá nhân (Individual)", "Yếu tố trong bản thân sinh viên", "Sợ sai (perfectionism): 'Tôi phải dịch hoàn hảo, một lỗi cũng không được'"],
  ["Nhóm 2. Đầu vào (Input)", "Thứ sinh viên phải tiếp nhận", "Người nói nói quá nhanh, ghi chú kịp"],
  ["Nhóm 3. Ghi chú (Note-taking)", "Kỹ năng ghi chú khi nghe", "Đọc lại chữ mình đã ghi không hiểu"],
  ["Nhóm 4. Đầu ra (Output)", "Kỹ năng truyền đạt khi nói", "Ngập ngừng, quên từ giữa chừng"],
  ["Nhóm 5. Môi trường (Environmental)", "Hoàn cảnh xung quanh", "Tiếng ồn, sợ bị bạn cùng lớp cười"],
  ["Nhóm 6. Liên quan giảng viên (Teacher-related)", "Người dạy và cách dạy", "Tiêu chí chấm rõ ràng, sửa lỗi tức thì"],
]));
bodyChildren.push(note("Ghi chú minh bạch: khung 6 nhóm lấy từ Ferdowsi và Razmi (2024). Nghiên cứu này có lỗi biên tập (sót chỗ trống chưa điền, bảng xếp hạng không khớp văn bản), nên đề tài CHỈ mượn khung khái niệm, không dùng các con số tần suất của họ làm bằng chứng. Đây là ví dụ của nguyên tắc: mỗi nguồn phải được đánh giá chất lượng trước khi dùng."));

// ── 4. Thang đo ──
bodyChildren.push(h1("4. Đo nỗi lo âu bằng gì: giới thiệu về thang đo"));
bodyChildren.push(body("Câu hỏi đặt ra: nỗi lo âu là thứ không nhìn thấy, không cầm nắm được — làm sao đưa nó thành con số? Câu trả lời của tâm lý học đo lường là thang đo (scale): một bộ câu hỏi được thiết kế cẩn thận, mỗi câu trả lời mang điểm, tổng điểm phản ánh mức độ của thứ cần đo. Ví dụ đời thường: cái cân phản ánh cân nặng bằng kg; thang lo âu phản ánh mức lo âu bằng điểm. Cân phải được kiểm định chuẩn xác trước khi dùng; thang cũng vậy."));
bodyChildren.push(body("Đề tài này dùng hai thang chính. Thứ nhất, thang Dong-20 cho RQ1: 20 câu, mỗi câu trả lời theo thang Likert 5 điểm (kiểu trả lời: 1 = hoàn toàn không đồng ý, 2 = không đồng ý, 3 = trung lập, 4 = đồng ý, 5 = hoàn toàn đồng ý). Điểm tổng chạy từ 20 (toàn bộ 20 câu đều chấm 1) đến 100 (toàn bộ chấm 5). Thang này có ưu điểm lớn: đã được kiểm định trên 245 sinh viên Trung Quốc với độ tin cậy Cronbach alpha bằng 0,92 (con số này nghĩa là gì sẽ học kỹ ở Bài 4; tạm hiểu: gần 1 là rất tin cậy)."));
bodyChildren.push(body("Thứ hai, bộ 30 câu cho RQ2: do chính đề tài soạn — nên trong ngôn ngữ nghiên cứu gọi là researcher-developed, pending pilot validation: tự phát triển, chờ kiểm định qua khảo sát thử. Điều này phải nói thẳng, không được gọi là thang đã chuẩn hóa, vì chưa ai kiểm chứng nó bao giờ. Kế hoạch kiểm định gồm: dịch xuôi - ngược (hai người dịch độc lập rồi đối chiếu), chuyên gia duyệt nội dung, phỏng vấn nhận thức 3-5 sinh viên (hỏi xem họ hiểu câu hỏi theo ý mình hay không), rồi khảo sát thử (pilot) 25-30 người để tính độ tin cậy."));
bodyChildren.push(body("Vì sao tốn công vậy? Vì một câu hỏi nghe có vẻ rõ ràng với người soạn nhưng có thể bị hiểu sai. Ví dụ: câu 'Tôi lo lắng khi phiên dịch trước lớp' — có sinh viên hiểu là trước cả lớp đông (sợ公众), có sinh viên hiểu là trước giảng viên (sợ bị chấm). Hai cách hiểu cho hai con số khác nhau; nếu không phát hiện từ sớm, toàn bộ dữ liệu bị nhiễu. Kiểm định công cụ là cách phát hiện sớm."));

// ── 5. Vai trò của bạn trong đề tài ──
bodyChildren.push(h1("5. Bạn đóng vai trò gì trong đề tài này"));
bodyChildren.push(body("Khóa luận là của bạn, nên mọi quyết định quan trọng đều thuộc về bạn (và giảng viên hướng dẫn — người thầy phụ trách chấm và duyệt đề tài, viết tắt GVHD). Trợ lý nghiên cứu lo phần việc kỹ thuật: kiểm tra tài liệu, soạn công cụ, tính toán, viết nháp tiếng Anh, và dạy bạn hiểu từng bước. Nhưng những quyết định như giữ phiếu 50 câu hay rút còn 30 câu, phỏng vấn thêm giảng viên hay không, tiến độ bao lâu — thuộc về bạn và GVHD; trợ lý sẽ luôn trình ít nhất hai phương án kèm khuyến nghị để bạn chọn, không tự quyết thay."));
bodyChildren.push(body("Điều bạn cần mang theo cho phiên làm việc tới: (1) bản nháp cũ nếu còn (bản đề cương 7 mục, bảng 30 câu, bản dịch tiếng Việt thang Dong-20 — nếu đã mất thì nói rõ để làm lại từ đầu); (2) tên học phần phiên dịch, học kỳ nào, số tín chỉ, sĩ số dự kiến — thông tin này nằm trong chương trình đào tạo (curriculum) của khoa và ảnh hưởng trực tiếp tới phần mẫu nghiên cứu và tiến độ; (3) các câu bạn muốn hỏi giảng viên hướng dẫn trong buổi gặp tới."));
bodyChildren.push(body("Bài tiếp theo (Bài 1) sẽ đi sâu vào loại tài liệu gọi là tài liệu nghiên cứu: bài báo tạp chí là gì, DOI là gì, vì sao có nguồn được tin và nguồn bị cảnh báo, và cách đọc một bài báo trong 10 phút. Sau đó Bài 2 dạy kỹ thang Dong-20, Bài 3 dạy bộ 30 câu, Bài 4 dạy các con số thống kê (trung bình, độ lệch chuẩn, alpha), Bài 5 dạy phân tích phỏng vấn."));

// ── 6. Tự kiểm tra cuối bài ──
bodyChildren.push(h1("6. Tự kiểm tra cuối bài"));
bodyChildren.push(body("Trả lời ba câu sau bằng lời của chính bạn, không nhìn lại văn bản. Nếu làm được cả ba, bạn đã sẵn sàng cho Bài 1."));
bodyChildren.push(quizBox([
  "Ba câu hỏi nghiên cứu của đề tài là gì, và mỗi câu được trả lời bằng công cụ nào?",
  "Vì sao RQ3 (phỏng vấn) phải đến sau RQ1 và RQ2 (khảo sát), mà không ngược lại?",
  "Vì sao bộ 30 câu không được gọi là thang đo đã chuẩn hóa, và phải làm gì trước khi dùng nó khảo sát thật?",
]));
bodyChildren.push(body("Đáp án gợi ý (chỉ mở ra sau khi đã tự trả lời): Câu 1 — RQ1 mức độ lo âu bằng thang Dong-20; RQ2 xếp hạng 6 nhóm yếu tố bằng bộ 30 câu tự phát triển; RQ3 lý do bằng phỏng vấn sâu 10-12 sinh viên. Câu 2 — vì phỏng vấn cần biết trước kết quả khảo sát để hỏi đúng chỗ sâu; làm ngược lại thì không biết đào đâu, và lời kể ít người không đủ sức xếp hạng. Câu 3 — vì nó chưa từng được kiểm chứng trên đối tượng nào; phải qua dịch xuôi - ngược, chuyên gia duyệt, phỏng vấn nhận thức và khảo sát thử rồi mới đủ độ tin cậy để dùng."));

// ══════════════ LẮP TÀI LIỆU ══════════════
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: { ascii: "Times New Roman", eastAsia: "Times New Roman" }, size: 24, color: "000000" },
        paragraph: { spacing: { line: 312 } },
      },
      heading1: {
        run: { font: { ascii: "Times New Roman", eastAsia: "Times New Roman" }, size: 32, bold: true, color: "000000" },
        paragraph: { spacing: { before: 360, after: 160, line: 312 } },
      },
      heading2: {
        run: { font: { ascii: "Times New Roman", eastAsia: "Times New Roman" }, size: 28, bold: true, color: "000000" },
        paragraph: { spacing: { before: 240, after: 120, line: 312 } },
      },
    },
  },
  sections: [
    // Section 1: Bìa R5 — margin 0 (bắt buộc: wrapper 16838 phủ toàn trang), không số trang
    {
      properties: { page: { size: pgSize, margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCoverR5({
        schoolName: "SỔ TAY HỌC TẬP KÈM THEO KHÓA LUẬN",
        title: "Bài 0: Đề tài hỏi gì và đo bằng cách nào",
        subtitle: "Yếu tố gây lo âu trong phiên dịch đuổi ở sinh viên năm ba ngành Ngôn ngữ Anh, HCMUE",
        metaLines: [
          "Người học: Sinh viên thực hiện khóa luận",
          "Trợ lý nghiên cứu: A4 - Gia sư",
          "Phiên bản: Bài 0, ngày 17 tháng 11 năm 2026",
        ],
        footerRight: "Dành riêng cho người mới bắt đầu phương pháp nghiên cứu",
      }),
    },
    // Section 2: Mục lục — số La Mã
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.UPPER_ROMAN } },
      },
      footers: { default: pageNumFooter() },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 480, after: 360 },
          children: [new TextRun({ text: "MỤC LỤC", bold: true, size: 32,
            font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
        }),
        new TableOfContents("Muc luc", { hyperlink: true, headingStyleRange: "1-2" }),
        new Paragraph({
          spacing: { before: 200 },
          children: [new TextRun({
            text: "Ghi chú: Mục lục tạo bằng trường tự động. Sau khi chỉnh sửa tài liệu, hãy nhấp chuột phải vào mục lục rồi chọn Update Field để cập nhật số trang chính xác.",
            italics: true, size: 18, color: "888888",
            font: { ascii: "Times New Roman", eastAsia: "Times New Roman" } })],
        }),
        // Không PageBreak cuối section: section 3 đã là NEXT_PAGE, thêm PageBreak sẽ tạo trang trắng
      ],
    },
    // Section 3: Thân bài — số Ả Rập từ 1
    {
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } },
      },
      footers: { default: pageNumFooter() },
      children: bodyChildren,
    },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/home/z/my-project/download/So_tay_hoc_tap_Bai_0.docx", buf);
  console.log("OK: So_tay_hoc_tap_Bai_0.docx", buf.length, "bytes");
});
