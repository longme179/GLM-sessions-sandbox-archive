// gen_bai1.js — Sổ tay học tập Bài 1 (tiếng Việt): tài liệu nghiên cứu & chất lượng nguồn
// Tái dùng kiến trúc Bài 0: bìa R5 margin-0 + TOC La Mã + thân Ả Rập; TNR toàn bộ.
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

// ── R5 meta table (theo design-system.md) ──
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
function body(text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 480 },
    spacing: { line: 312, after: 80 },
    children: [new TextRun({ text, size: 24, color: "000000", font: FONT })],
  });
}
function note(text) {
  return new Paragraph({
    alignment: AlignmentType.LEFT, spacing: { line: 312, before: 60, after: 160 },
    children: [new TextRun({ text, size: 21, color: "404040", italics: true, font: FONT })],
  });
}
function quizBox(qs) {
  const border = { style: BorderStyle.SINGLE, size: 4, color: "555555" };
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { top: border, bottom: border, left: border, right: border, insideHorizontal: NB, insideVertical: NB },
    rows: [new TableRow({
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: "F5F5F0" },
        margins: { top: 120, bottom: 120, left: 200, right: 200 },
        width: { size: 100, type: WidthType.PERCENTAGE },
        children: [
          new Paragraph({ spacing: { line: 312, after: 60 },
            children: [new TextRun({ text: "Tự kiểm tra", bold: true, size: 24, font: FONT })] }),
          ...qs.map((q, i) => new Paragraph({ spacing: { line: 312, after: 40 },
            children: [new TextRun({ text: (i + 1) + ". " + q, size: 24, font: FONT })] })),
        ],
      })],
    })],
  });
}
function mkTable(header, rows, widths) {
  const mkCell = (text, isHeader, w) => new TableCell({
    width: { size: w, type: WidthType.PERCENTAGE },
    shading: isHeader ? { type: ShadingType.CLEAR, fill: "EFEFE8" } : undefined,
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    children: [new Paragraph({ spacing: { line: 312 },
      children: [new TextRun({ text, bold: isHeader, size: 21, font: FONT })] })],
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

// ══════════════ NỘI DUNG ══════════════
const B = [];

B.push(h1("Lời mở đầu: vì sao phải học cách đọc nguồn"));
B.push(body("Bài 0 đã trả lời đề tài hỏi gì. Bài 1 dạy một kỹ năng bạn sẽ dùng mỗi tuần từ giờ đến khi nộp khóa luận: đọc và đánh giá tài liệu nghiên cứu. Đây không phải kỹ năng văn phòng: việc gìn răng giữ tiếng của khóa luận nằm ở chỗ mỗi con số, mỗi câu trích dẫn đều lần ra được nguồn gốc. Trong phiên kiểm tra tài liệu vừa qua, trợ lý đã mở toàn văn sáu nguồn chính của đề tài và phát hiện đủ thứ vấn đề - từ lỗi biên tập thô đến tạp chí bình duyệt chỉ ba ngày. Nếu không biết nhìn những dấu hiệu đó, bạn có thể vô tình dựng cả đề cương trên một bài báo yếu."));
B.push(body("Bài này dùng đúng các nguồn thật của đề tài làm ví dụ dạy, nên mọi thứ bạn học được đều dùng lại được ngay. Bốn phần: (1) bài báo khoa học là gì và các loại tài liệu khác nhau ra sao; (2) DOI và cách kiểm tra một nguồn còn sống hay không; (3) bốn dấu hiệu nguồn yếu, kèm ví dụ thật đã bắt gặp; (4) cách đọc một bài báo trong mười phút cho người bận rộn."));

B.push(h1("1. Bài báo khoa học là gì, và các loại tài liệu"));
B.push(body("Tài liệu nghiên cứu có nhiều loại, không phải loại nào cũng đáng tin ngang nhau. Loại đứng đầu là bài báo bình duyệt (peer-reviewed journal article): tác giả gửi bài cho tạp chí, ban biên tập gửi tiếp cho hai hoặc ba chuyên gia giấu tên trong ngành để soi lỗi; qua được mới đăng. Ví dụ trong đề tài: bài của Horwitz, Horwitz và Cope năm 1986 trên tạp chí The Modern Language Journal - bài cha đẻ của thang FLCAS - là một bài bình duyệt kinh điển, được trích hơn chục nghìn lần."));
B.push(body("Loại thứ hai là luận án (thesis, dissertation): nghiên cứu dài hàng trăm trang cho bằng tiến sĩ hoặc thạc sĩ, thường chỉ có một giảng viên hướng dẫn cùng hội đồng chấm, không qua bình duyệt tạp chí. Ưu điểm: cực kỳ chi tiết (toàn bộ bảng hỏi thường nằm nguyên trong phụ lục - luận án của Chiang 2006 chứa thang ICAS 44 câu ở Appendix A, trang 203-220). Nhược điểm: chất lượng tùy từng bài, và chưa ai kiểm chứng chéo như bài báo. Loại thứ ba là hội nghị (conference paper) và tài liệu chưa công bố. Loại cuối, cẩn trọng nhất: preprint - bản viết xong chưa qua bình duyệt, đăng lên kho mở trước."));
B.push(body("Đề tài của bạn dùng cả hai loại: thang Dong-20 gốc là bài báo tạp chí (Dong, Chen và Yu, 2013, tạp chí Foreign Language World của Trung Quốc), còn thang ICAS lấy từ luận án Chiang. Cách dùng khác nhau: bài báo có thể trích số độ tin cậy đã công bố; luận án thì nên ghi rõ trích từ luận án, kèm năm và trường."));

B.push(h1("2. DOI: mã số định danh của một bài báo"));
B.push(body("DOI (Digital Object Identifier, định danh đối tượng số) là mã định danh duy nhất của một tài liệu số, giống số căn cước công dân của bài báo: ví dụ 10.3389/fpsyg.2025.1671239 là của bài Wang 2025. Ưu điểm so với đường link thường: link có thể chết, DOI thì vĩnh viễn - gõ https://doi.org/ trước mã là tới trang bài báo, kể cả khi tạp chí đổi nhà xuất bản."));
B.push(body("Cách dùng trong thực tế: khi đọc bất kỳ bài nào, tìm DOI (thường ở đầu bài hoặc trong chi tiết trích dẫn); mở https://doi.org/[mã] để chắc chắn bạn đang trúng đúng bài, không phải bản nháp hay bài trùng tên. Khi viết khóa luận, trích dẫn theo APA 7 luôn kèm DOI nếu có. Trong phiên kiểm tra vừa rồi, trợ lý đã đối chiếu DOI của cả sáu nguồn: bốn nguồn mở đúng bài; hai nguồn (Dong 2013 và Chiang 2006) không mở được toàn văn nên mọi con số từ chúng phải gắn nhãn chưa xác minh cho tới khi tự mắt đọc được."));
B.push(body("Một lưu ý thực tế: DOI tồn tại không có nghĩa nội dung tốt - mã DOI chỉ xác định bài, không thẩm định chất lượng. Đó là việc của phần tiếp theo."));

B.push(h1("3. Bốn dấu hiệu nguồn yếu - ví dụ thật của đề tài"));
B.push(body("Dưới đây là bốn dấu hiệu trợ lý đã thật sự bắt gặp khi mở toàn văn các nguồn của đề tài. Đây là phần quan trọng nhất của bài."));

B.push(h2("3.1. Dấu hiệu 1: lỗi biên tập còn sót"));
B.push(body("Bài Ferdowsi và Razmi (2024) - nguồn cung cấp khung sáu nhóm yếu tố cho đề tài - vẫn còn sót chỗ trống viết sẵn dạng [insert location] (nghĩa là địa điểm nghiên cứu chưa được điền vào), có câu lặp nguyên văn, và bảng 1 ghi rõ sắp xếp từ cao xuống thấp nhưng dòng 15 điểm lại đứng trước dòng 18 điểm. Một bài được biên tập kỹ không để sót những lỗi thô thế này. Vì sao vẫn dùng? Vì khung khái niệm sáu nhóm của họ rõ ràng và hữu ích, và bài được xuất bản mở theo giấy phép CC-BY. Nguyên tắc rút ra: dùng phần tốt, khai báo phần lỗi, không dùng số liệu định lượng của bài này làm bằng chứng."));

B.push(h2("3.2. Dấu hiệu 2: bình duyệt quá nhanh"));
B.push(body("Bài Tran (2025) - nguồn năm câu hỏi nguyên văn duy nhất của đề tài - đăng trên tạp chí IJRISS. Tra cứu cho thấy: tạp chí này không có mặt trong danh mục DOAJ (thư mục tạp chí mở chất lượng), và khoảng thời gian từ khi nhận bài đến khi đăng chỉ ba ngày. Bình duyệt thật sự (hai ba vòng chuyên gia đọc, góp ý, sửa) hiếm khi nhanh vậy. Kết luận sử dụng: năm câu hỏi nguyên văn vẫn dùng được vì đó là dữ liệu khảo sát cụ thể, nhưng mọi lập luận lớn không nên dựng riêng trên bài này - phải có nguồn khác cùng nói."));

B.push(h2("3.3. Dấu hiệu 3: mô tả lệch so với nguồn gốc"));
B.push(body("Bài Wang (2025) dùng thang Dong-20 nhưng tự đổi tên ba chiều và tự gán lại câu vào chiều theo cách riêng (chỉ gán được 13 trên 20 câu), không báo cáo độ tin cậy Cronbach alpha. Nếu ai đó đọc Wang và tưởng đó là cấu trúc gốc của thang Dong thì sẽ trích sai trong khóa luận. Đây là lý do đề tài luôn quay về bản gốc Dong 2013 cho mọi thông số của thang. Nguyên tắc: khi một nghiên cứu dùng lại thang của người khác, đối chiếu lại với nguồn gốc - bản gốc luôn thắng mô tả thứ cấp."));

B.push(h2("3.4. Dấu hiệu 4: không mở được toàn văn"));
B.push(body("Mọi con số chưa tự đọc được trong toàn văn đều phải gắn nhãn chưa xác minh. Trong phiên kiểm tra, hai nguồn bị bot chặn đường tải (ResearchGate của Dong 2013 và kho luận án Đại học Texas của Chiang 2006); trợ lý đã thử tổng cộng hơn mười đường khác nhau - bản sao trên các kho khác, máy chủ lưu trữ web, thư mục học thuật - đều bị chặn. Kết quả: những con số của Dong 2013 như n=245 hay hệ số tương quan -0,434 tạm giữ nhãn chưa xác minh cho tới khi tải được bản gốc (trợ lý đã xin bạn tải bằng trình duyệt thật ở nhà). Đây là kỷ luật: không có nghĩa là chưa có - chỉ là chưa kiểm chứng được, và phải nói rõ."));

B.push(tableTitle("Bảng 1. Bốn dấu hiệu và cách xử lý - tóm tắt"));
B.push(mkTable(
  ["Dấu hiệu", "Ví dụ thật trong đề tài", "Cách xử lý"],
  [
    ["Lỗi biên tập sót", "Ferdowsi & Razmi 2024: sót [insert location], bảng sai thứ tự", "Chỉ dùng khung khái niệm; không dùng số liệu của họ làm bằng chứng"],
    ["Bình duyệt quá nhanh", "Tran 2025 trên IJRISS: 3 ngày, không có DOAJ", "Dùng 5 item nguyên văn; không dựng lập luận lớn riêng trên bài này"],
    ["Mô tả lệch nguồn gốc", "Wang 2025 đổi tên chiều, gán lại 13/20 câu thang Dong", "Luôn quay về bản gốc 2013 cho thông số thang"],
    ["Không mở được toàn văn", "Dong 2013 (RG chặn), Chiang 2006 (UT Austin chặn)", "Gắn nhãn chưa xác minh; nhờ người tải bản gốc; không đoán"],
  ],
  [22, 40, 38]));
B.push(note("Bốn ví dụ trên đều là kết quả mở toàn văn thật trong phiên 2026-11-17, không phải ví dụ tưởng tượng. Bằng chứng được lưu trong thư mục source-verification-evidence."));

B.push(h1("4. Đọc một bài báo trong mười phút"));
B.push(body("Bạn không cần đọc từng chữ. Quy trình năm bước, mỗi bước hai phút. Bước 1: đọc tóm tắt (abstract) - biết bài hỏi gì, làm gì, ra kết quả gì. Bước 2: lướt phần Thảo luận (Discussion) và Kết luận (Conclusion) - chỗ tác giả nói rõ ý nghĩa. Bước 3: xem bảng và hình - bảng là kết quả cô đặc nhất. Bước 4: đọc kỹ đúng phần liên quan đến đề tài của bạn (ví dụ: phụ lục bảng hỏi, phần độ tin cậy). Bước 5: ghi lại ngay một dòng trích dẫn APA kèm DOI và ghi chú dùng được gì - làm ngay kẻo quên."));
B.push(body("Mẹo cho đề tài này: khi đọc bài về lo âu phiên dịch, tìm ngay ba thứ - (1) thang đo nào được dùng (Dong? ICAS? FLCAS? tự viết?), (2) mẫu bao nhiêu người, ai (sinh viên năm mấy), (3) độ tin cậy Cronbach alpha bao nhiêu. Ba thông tin đó đủ để biết bài có so sánh được với đề tài của bạn hay không. Ví dụ: Wang 2025 dùng thang Dong với 47 sinh viên nhưng không báo cáo alpha - vậy không so sánh độ tin cậy được; Xing 2025 (tạp chí của nhóm Nature) báo cáo đủ số liệu và mẫu 64 người - so sánh được."));
B.push(body("Câu hỏi cuối khi đọc xong luôn là: bài này giúp trả lời RQ nào của tôi, và tôi trích nó cho ý gì? Nếu không trả lời được thì ghi vào sổ tài liệu thừa, đừng nhét vào khóa luận cho đẹp danh mục trích dẫn."));

B.push(h1("5. Tự kiểm tra cuối bài"));
B.push(body("Trả lời bằng lời của bạn trước khi mở đáp án."));
B.push(quizBox([
  "DOI là gì, và vì sao DOI tốt hơn đường link thường? Nếu một bài có DOI, điều đó có bảo đảm bài tốt không?",
  "Kể tên hai dấu hiệu nguồn yếu trong bốn dấu hiệu đã học, kèm ví dụ thật từ chính các nguồn của đề tài.",
  "Bạn có ba nguồn: một bài báo bình duyệt 1986 được trích cả nghìn lần, một bài 2025 bình duyệt ba ngày, một luận án 2006 có phụ lục thang đo. Mỗi nguồn dùng được cho gì trong đề tài?",
]));
B.push(body("Đáp án gợi ý: Câu 1 - DOI là mã định danh vĩnh viễn của tài liệu số, mở qua https://doi.org/[mã]; nó tốt hơn link vì link chết còn DOI không; nhưng DOI chỉ định danh, không thẩm định chất lượng. Câu 2 - ví dụ: lỗi biên tập sót (Ferdowsi & Razmi 2024 còn [insert location]); bình duyệt ba ngày (Tran 2025 trên IJRISS). Câu 3 - bài 1986 (FLCAS): nền lý thuyết và item phỏng theo; bài 2025: dữ liệu bối cảnh Việt Nam và 5 item nguyên văn, dùng chọn lọc; luận án 2006: trích nguyên văn thang ICAS từ phụ lục, ghi rõ là luận án chưa qua bình duyệt tạp chí."));

B.push(h1("6. Sẵn sàng cho Bài 2"));
B.push(body("Bài 2 sẽ đi sâu vào thang Dong-20: ba chiều, cách tính điểm, đảo điểm, và ý nghĩa từng hệ số độ tin cậy của bản gốc. Để học hiệu quả nhất, bạn nên chuẩn bị bản PDF gốc Dong 2013 (trợ lý đã nhờ bạn tải) - bài học sẽ chỉ tay vào từng phần của bản gốc. Sau Bài 2, bạn sẽ đọc hiểu được mọi con số trong phần Công cụ của đề cương mà không cần dịch ngược."));

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
        schoolName: "SỔ TAY HỌC TẬP KÈM THEO KHÓA LUẬN",
        titleLines: ["Bài 1: Đọc và đánh giá", "tài liệu nghiên cứu"],
        titlePt: 33,
        subtitle: "Yếu tố gây lo âu trong phiên dịch đuổi ở sinh viên năm ba ngành Ngôn ngữ Anh, HCMUE",
        metaLines: [
          "Người học: Sinh viên thực hiện khóa luận",
          "Trợ lý nghiên cứu: A4 - Gia sư",
          "Phiên bản: Bài 1, ngày 17 tháng 11 năm 2026",
        ],
        footerRight: "Ví dụ trong bài lấy từ kết quả kiểm tra nguồn thật của đề tài",
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
  fs.writeFileSync("/home/z/my-project/download/So_tay_hoc_tap_Bai_1.docx", buf);
  console.log("OK: So_tay_hoc_tap_Bai_1.docx", buf.length, "bytes");
});
