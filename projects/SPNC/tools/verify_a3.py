#!/usr/bin/env python3
"""verify_a3.py — kiểm tra Chương 3 Methodology bằng code (khuôn verify_bai1.py)"""
import subprocess
import sys

PDF = "/home/z/my-project/download/Chuong3_Methodology_nhap.pdf"

def page_text(n):
    r = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), "-layout", PDF, "-"],
                       capture_output=True, text=True)
    return r.stdout

info = subprocess.run(["pdfinfo", PDF], capture_output=True, text=True).stdout
npages = int([l for l in info.splitlines() if l.startswith("Pages:")][0].split()[1])
print(f"pages: {npages}")
texts = {n: page_text(n) for n in range(1, npages + 1)}
errors = []

# 1) trang trắng
for n, t in texts.items():
    if len(t.strip()) < 20:
        errors.append(f"Trang {n} gần như trắng")

# 2) thứ tự mục
order = ["Phương pháp",  # bìa (tiêu đề 2 dòng: "Chương 3. Phương pháp" / "nghiên cứu (Methodology)")
         "nghiên cứu (Methodology)",
         "MỤC LỤC",
         "3.1. Thiết kế nghiên cứu",
         "3.2. Participants",
         "3.3. Công cụ nghiên cứu",
         "3.4. Quy trình kiểm định",
         "3.5. Thu thập dữ liệu",
         "3.6. Phân tích dữ liệu",
         "3.7. Đạo đức nghiên cứu",
         "3.8. Vị thế của nhà nghiên cứu"]
pos = -1
for marker in order:
    found = None
    for n in range(1, npages + 1):
        if marker in texts[n]:
            found = n
            break
    if found is None:
        errors.append(f"KHÔNG THẤY: {marker!r}")
    elif found < pos:
        errors.append(f"Sai thứ tự: {marker!r} (trang {found} < {pos})")
    else:
        pos = found
        print(f"  trang {found}: {marker[:40]}")

# 3) token xấu (placeholder [chờ U1/U2] là CÓ CHỦ ĐÍCH — phải tồn tại tối thiểu 4)
bad_tokens = ["XXX", "TODO", "undefined", "NaN", "【", "|---|", "**", "待补充"]
for n, t in texts.items():
    for tok in bad_tokens:
        if tok in t:
            errors.append(f"Trang {n}: token xấu {tok!r}")

# 4) placeholder có chủ đích phải đủ (đánh dấu cam trên docx)
all_text = "\n".join(texts.values())
for need_ph in ["chờ U2", "chờ U1", "chờ U5"]:
    if need_ph not in all_text:
        errors.append(f"Thiếu placeholder {need_ph!r} (dữ liệu chưa có phải được đánh dấu rõ)")

# 5) nội dung then chốt từ ledgers
for need in ["explanatory mixed-methods", "Dong-20", "đảo điểm", "Ferdowsi và Razmi (2024)",
             "researcher-developed", "Braun và Clarke (2006)", "Cronbach alpha .92",
             "item-total", "maximum variation", ".30", "EFA", "n≈100"]:
    if need not in all_text:
        errors.append(f"Thiếu nội dung: {need!r}")

# 6) bảng 3.1-3.3 tồn tại
for tbl in ["Bảng 3.1", "Bảng 3.2", "Bảng 3.3"]:
    if tbl not in all_text:
        errors.append(f"Thiếu {tbl}")

print()
if errors:
    print("LỖI:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"PASS: {npages} trang, thứ tự đúng, placeholder chờ U1/U2/U5 đủ, nội dung then chốt đủ, 3 bảng đủ.")
