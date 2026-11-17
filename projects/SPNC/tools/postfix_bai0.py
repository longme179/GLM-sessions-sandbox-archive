"""
#!/usr/bin/env python3
postfix_bai0.py — hậu kỳ docx Bài 0 (theo toc.md):
1. Footer section 2 (La Mã): PAGE -> PAGE \\* ROMAN \\* MERGEFORMAT
2. Footer section 3 (Ả Rập): PAGE -> PAGE \\* arabic \\* MERGEFORMAT
3. Xóa <w:pgNumType/> rỗng (bìa)
4. settings.xml: updateFields=true (Word tự hỏi update khi mở)
GHI CHÚ (bài học 2026-11-17): docx-js 9.15 đã tự sinh sẵn mục TOC đầu tiên
(hyperlink + PAGEREF, w:dirty=true → Word tự update khi mở). add_toc_placeholders.py
chèn THÊM các đoạn TOC1 → mục đầu bị LẶP. Vì vậy KHÔNG chạy script đó với docx-js 9.x;
chỉ cần updateFields. Nếu lỡ chạy rồi: xóa các đoạn TOC1 trùng (bước 5).
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path

DOCX = Path("/home/z/my-project/download/So_tay_hoc_tap_Bai_0.docx")
TMP = Path("/tmp/bai0_docx")

if TMP.exists():
    shutil.rmtree(TMP)
TMP.mkdir(parents=True)

with zipfile.ZipFile(DOCX) as z:
    z.extractall(TMP)

doc_xml = (TMP / "word" / "document.xml").read_text(encoding="utf-8")

# 3) xóa pgNumType rỗng
doc_xml, n_empty = re.subn(r"<w:pgNumType/>", "", doc_xml)

# tìm thứ tự các footer reference trong document.xml (theo thứ tự section)
rels_xml = (TMP / "word" / "_rels" / "document.xml.rels").read_text(encoding="utf-8")
rid_to_file = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(footer\d+\.xml)"', rels_xml))

footer_refs = re.findall(r'<w:footerReference w:type="default" r:id="(rId\d+)"/>', doc_xml)
print("footer refs theo thu tu section:", footer_refs, "->", [rid_to_file.get(r) for r in footer_refs])

# section 2 (mục lục) = footer đầu tiên, section 3 (thân) = footer thứ hai
patch_plan = []
if len(footer_refs) >= 1:
    patch_plan.append((rid_to_file[footer_refs[0]], "ROMAN"))
if len(footer_refs) >= 2:
    patch_plan.append((rid_to_file[footer_refs[1]], "arabic"))

for fname, fmt in patch_plan:
    f = TMP / "word" / fname
    xml = f.read_text(encoding="utf-8")
    xml2, n = re.subn(
        r"(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)",
        rf"\1 PAGE \\* {fmt} \\* MERGEFORMAT \2",
        xml)
    f.write_text(xml2, encoding="utf-8")
    print(f"patched {fname}: {n} PAGE field(s) -> {fmt}")

(TMP / "word" / "document.xml").write_text(doc_xml, encoding="utf-8")
print(f"removed {n_empty} empty pgNumType")

# 4) settings.xml: updateFields (để Word đề nghị update số trang khi mở)
settings = TMP / "word" / "settings.xml"
sxml = settings.read_text(encoding="utf-8")
if "updateFields" not in sxml:
    sxml = sxml.replace("<w:settings", "<w:settings", 1)
    # chèn phần tử vào đầu settings
    m = sxml.find(">", sxml.find("<w:settings"))
    sxml = sxml[:m + 1] + '<w:updateFields w:val="true"/>' + sxml[m + 1:]
    settings.write_text(sxml, encoding="utf-8")
    print("added updateFields=true to settings.xml")
else:
    print("updateFields already present")

# 5) outlineLvl cho Heading1-6 trong styles.xml (chức năng của add_toc_placeholders.py;
#    tự làm để KHÔNG phải chạy script đó — nó xung đột với docx-js 9.x đã tự sinh mục TOC)
styles = TMP / "word" / "styles.xml"
sxml2 = styles.read_text(encoding="utf-8")
n_out = 0
for lvl in range(1, 7):
    # chèn <w:outlineLvl w:val="N"/> vào cuối pPr của style HeadingN
    pat = re.compile(
        r'(<w:style [^>]*w:styleId="Heading' + str(lvl) + r'"[^>]*>.*?)(<w:pPr>)(.*?</w:pPr>)',
        re.DOTALL)
    m = pat.search(sxml2)
    if m and "outlineLvl" not in m.group(3):
        sxml2 = sxml2[:m.end(2)] + f'<w:outlineLvl w:val="{lvl - 1}"/>' + sxml2[m.end(2):]
        n_out += 1
styles.write_text(sxml2, encoding="utf-8")
print(f"added outlineLvl to {n_out} heading styles")

# đóng gói lại (ghi đè file gốc)
import os
out = zipfile.ZipFile(DOCX, "w", zipfile.ZIP_DEFLATED)
for root, _, files in os.walk(TMP):
    for name in files:
        full = Path(root) / name
        out.write(full, str(full.relative_to(TMP)))
out.close()
print("repacked:", DOCX, DOCX.stat().st_size, "bytes")
