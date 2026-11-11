# FOLLOWUP 2C — LÀM LẠI C3 (wizard add) bằng KEYBOARD: wtype CÓ hỗ trợ phím

## Sửa thông tin sai (quan trọng)

Trong prompt trước tôi ghi "wtype chỉ gõ văn bản" — SAI. Đó là chẩn đoán nhầm
của session khác. Bằng chứng: transcript round 1 (đã chạy 19/23 PASS trên
chính máy này) dùng nguyên các lệnh sau, verbatim:

```
niri msg action focus-window --id 459; sleep 0.3
for i in $(seq 1 11); do wtype -k Tab; sleep 0.1; done
wtype -k Return
wtype -M shift -k Tab -m shift
wtype -M ctrl -k r -m ctrl
```

wtype 0.4 hỗ trợ: `-k <keysym>` (Tab, Return, space, Up, Down, Escape,
BackSpace…), `-M <mod>` giữ modifier, `-m <mod>` nhả modifier, `-P` press,
`-p` release. Chuỗi "Usage: wtype <text-to-type>" chỉ là message khi gọi
không đối số — không phải danh sách đầy đủ.

Kỹ thuật điều khiển (round 1 đã chứng minh): focus cửa sổ → đếm Tab theo
thứ tự focus của trang → `wtype -k Return` để kích hoạt → `wtype "text"`
để gõ vào field đang focus. Tab order sidebar (từ App.svelte): node →
instance → "+ Add instance" → "Remove" → "Close app" → Start → Stop →
Restart → các tab Console/Settings/Properties/Mods/Notifications → nội
dung trang.

## Làm lại C3 (BUG-2 UI wizard) — các bước

1. Relaunch GUI như C1 (MINEWRAP_CONFIG + XDG_CONFIG_HOME như cũ, port
   8097, KHÔNG :5173). Đợi /health OK. Có thể start g3 cho console có dữ
   liệu (không bắt buộc).
2. Đọc `ui/src/components/Wizard.svelte` + `AddInstance.svelte` để biết:
   field nào bắt buộc, giá trị default, thứ tự DOM (để đếm Tab), nút submit
   label gì. Work dir dùng sẵn: `/home/kimhoanglong/dev-memtest/work/g3/
   g3add-server` (có stub jar từ round 1 — Scan sẽ tìm thấy; kiểm tra còn
   tồn tại, không thì copy từ work/g3/server).
3. Focus Minewrap → Tab tới nút "+ Add instance" (đếm từ đầu; nếu không
   chắc, dùng screenshot trước đó chỉ để ĐỐI CHIẾU SAU bằng REST — không
   đọc ảnh) → `wtype -k Return` → wizard mở.
4. Điền form (ID = `g3r2c`, Display name = `G3 Round2C`, Work dir như
   trên; các field khác giữ default nếu được; nếu bắt buộc java path → gõ
   đường dẫn fakejava-echo; RAM/preset/launch-mode giữ default — tránh
   đụng <select> trừ khi bắt buộc). Giữa các field: `wtype -k Tab`. Gõ:
   `wtype "giá trị"`. Nếu cần xóa text cũ: `wtype -M ctrl -k a -m ctrl`
   rồi `wtype -k BackSpace`.
5. Submit (Tab tới nút Add/Create → `wtype -k Return`). Nếu có confirm
   dialog → `wtype -k Return` (OK mặc định).
6. REST đối chiếu: `GET /api/v1/instances` có `g3r2c` → lưu
   `c3-instances.json`. YÊU CẦU: KHÔNG có lỗi decode hiển thị (nếu form
   hiện lỗi gì, chụp + ghi verbatim).
7. `grim` → `shot-c3-wizard.png` (form đã submit) và `shot-c4-added.png`
   (sidebar có g3r2c).
8. Remove `g3r2c`: Tab tới "Remove" → Return → confirm → REST xác nhận
   biến mất → `shot-c4-removed.png`.
9. Dọn máy như C5 (kill đúng PID GUI + daemon sidecar + fakejava; ports
   free; KHÔNG pkill -f).
10. Cập nhật `REPORT-2C.md`: đổi dòng C3 từ UNVERIFIED → kết quả thật
    (PASS/FAIL + bằng chứng), cập nhật kết luận. Tin nhắn cuối ≥300 ký tự.

## Giữ nguyên các quy tắc
- KHÔNG đọc ảnh vào context (chỉ grim lưu file). Tool output gọn (head).
- Focus cửa sổ trước mỗi chuỗi phím; refocus Firefox của user sau mỗi
  chuỗi thao tác.
- Không sửa code, không commit. Token không vào file/report.
- Nếu sau ~10 lần thử hợp lý vẫn không drive được form → ghi FAIL/UNVERIFIED
  chi tiết (đã thử gì, kết quả từng bước, bằng chứng REST), KHÔNG bịa.
