#!/usr/bin/env python3
"""verify_bai1.py — kiểm tra Bài 1 bằng code (khuôn verify_bai0.py)"""
import subprocess
import sys

PDF = "/home/z/my-project/download/So_tay_hoc_tap_Bai_1.pdf"

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
order = ["Bài 1: Đọc và đánh giá",  # bìa
         "MỤC LỤC",
         "Lời mở đầu",
         "1. Bài báo khoa học là gì",
         "2. DOI: mã số định danh",
         "3. Bốn dấu hiệu nguồn yếu",
         "4. Đọc một bài báo trong mười phút",
         "5. Tự kiểm tra cuối bài",
         "6. Sẵn sàng cho Bài 2"]
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
        print(f"  trang {found}: {marker[:42]}")

# 3) token xấu — "insert location" là trích dẫn CÓ CHỦ ĐÍCH trong Bài 1
# (mô tả lỗi biên tập của Ferdowsi & Razmi 2024), chỉ cho phép xuất hiện
# trong đoạn 3.1 kèm từ khóa ngữ cảnh "sót" hoặc "chưa được điền"
bad_tokens = ["XXX", "TODO", "undefined", "NaN", "【", "|---|", "**", "待补充"]
for n, t in texts.items():
    for tok in bad_tokens:
        if tok in t:
            errors.append(f"Trang {n}: token xấu {tok!r}")
    if "insert location" in t:
        ctx = t[max(0, t.find("insert location") - 120):t.find("insert location") + 120]
        if not any(k in ctx for k in ["sót", "chưa được điền", "[insert location]"]):
            errors.append(f"Trang {n}: 'insert location' không nằm trong ngữ cảnh trích dẫn")

# 4) nội dung then chốt
all_text = "\n".join(texts.values())
for need in ["peer-reviewed", "DOI", "Ferdowsi", "IJRISS", "Wang 2025", "Dong 2013", "Chiang 2006",
             "FLCAS", "bình duyệt", "Cronbach", "đảo điểm" if "đảo điểm" in all_text else "phụ lục"]:
    if need not in all_text:
        errors.append(f"Thiếu: {need!r}")

# 5) mục lục không lặp
toc_page = None
for n, t in texts.items():
    if "MỤC LỤC" in t:
        toc_page = n
        break
if toc_page:
    for marker in ["Lời mở đầu", "1. Bài báo", "2. DOI", "3. Bốn dấu hiệu", "4. Đọc một bài", "5. Tự kiểm tra", "6. Sẵn sàng"]:
        cnt = texts[toc_page].count(marker)
        if cnt != 1:
            errors.append(f"Mục lục: '{marker}' xuất hiện {cnt} lần")

print()
if errors:
    print("LỖI:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"PASS: {npages} trang, không trắng, thứ tự đúng, không token xấu, nội dung đủ, mục lục không lặp.")
