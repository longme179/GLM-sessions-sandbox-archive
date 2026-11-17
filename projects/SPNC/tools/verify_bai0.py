#!/usr/bin/env python3
"""verify_bai0.py — kiểm tra Bài 0 bằng code (model không xem được ảnh).
1. Mỗi trang PDF phải có nội dung (không trang trắng)
2. Thứ tự các mục đúng: bìa -> mục lục -> Lời mở đầu -> 1..6
3. Không trùng đoạn, không placeholder sót (XXX, TODO, 【, undefined, NaN, markdown)
4. Bảng 1 + Bảng 6 nhóm xuất hiện đủ hàng
"""
import subprocess
import sys

PDF = "/home/z/my-project/download/So_tay_hoc_tap_Bai_0.pdf"

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
        errors.append(f"Trang {n} gần như trắng ({len(t.strip())} ký tự)")

# 2) thứ tự mục
order = ["Bài 0: Đề tài hỏi gì",  # bìa (tiêu đề)
         "MỤC LỤC",
         "Lời mở đầu",
         "1. Đề tài này hỏi cái gì",
         "2. Ba câu hỏi nghiên cứu",
         "3. Sáu nhóm yếu tố",
         "4. Đo nỗi lo âu bằng gì",
         "5. Bạn đóng vai trò gì",
         "6. Tự kiểm tra cuối bài"]
pos = -1
for marker in order:
    found_page = None
    for n in range(1, npages + 1):
        if marker in texts[n]:
            found_page = n
            break
    if found_page is None:
        errors.append(f"KHÔNG THẤY mục: {marker!r}")
    elif found_page < pos:
        errors.append(f"Mục {marker!r} xuất hiện sai thứ tự (trang {found_page} < {pos})")
    else:
        pos = found_page
        print(f"  trang {found_page}: {marker[:45]}")

# 3) placeholder / ký tự dở
bad_tokens = ["XXX", "TODO", "undefined", "NaN", "【", "】", "|---|", "**", "待补充", "____"]
for n, t in texts.items():
    for tok in bad_tokens:
        if tok in t:
            errors.append(f"Trang {n}: sót token xấu {tok!r}")

# 4) bảng đủ hàng
all_text = "\n".join(texts.values())
for need in ["RQ1. Mức độ lo âu", "RQ2. Nhóm yếu tố nào", "RQ3. Vì sao lại như vậy",
             "Cá nhân", "Đầu vào", "Ghi chú", "Đầu ra", "Môi trường", "giảng viên"]:
    if need not in all_text:
        errors.append(f"Thiếu nội dung bảng/danh sách: {need!r}")

# 5b) mục lục: mỗi tiêu đề chỉ xuất hiện đúng 1 dòng có số trang (không lặp)
toc_page = None
for n, t in texts.items():
    if "MỤC LỤC" in t:
        toc_page = n
        break
if toc_page:
    toc_text = texts[toc_page]
    for marker in ["Lời mở đầu", "1. Đề tài", "2. Ba câu hỏi", "3. Sáu nhóm",
                   "4. Đo nỗi lo âu", "5. Bạn đóng vai trò", "6. Tự kiểm tra"]:
        cnt = toc_text.count(marker)
        if cnt != 1:
            errors.append(f"Mục lục: '{marker}' xuất hiện {cnt} lần (phải đúng 1)")

# 5) trùng lặp đoạn (mỗi đoạn body >=60 ký tự chỉ được xuất hiện 1 lần)
import re
paras = [p.strip() for p in all_text.split("\n") if len(p.strip()) >= 60]
seen = {}
for p in paras:
    key = p[:80]
    seen[key] = seen.get(key, 0) + 1
for k, c in seen.items():
    if c > 1:
        errors.append(f"Đoạn lặp {c} lần: {k[:60]!r}")

print()
if errors:
    print("LỖI:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"PASS: {npages} trang, không trắng, thứ tự đúng, không placeholder, không lặp, bảng đủ.")
