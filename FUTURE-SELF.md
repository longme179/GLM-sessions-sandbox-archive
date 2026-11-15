# Lời nhắn nhủ cho bản thân tương lai (FUTURE-SELF)

Gửi tôi — của tương lai,

Nếu bạn đang đọc file này thì sandbox vừa reset, hoặc một session mới vừa bắt
đầu. Đừng vội. Đọc cái này trước.

## Bạn phục vụ ai

Người dùng là `longme179` (GitHub) / `kimhoanglong` (máy desktop Fedora + Niri
của họ). Máy đó chạy Quickshell shell của riêng họ — repo
`lme-fedora-niri-qs` — và họ giao việc qua một IM gateway; phần code chạy qua
OpenCode agent trên chính máy desktop của họ (gateway URL + Basic Auth do họ
cấp lại mỗi session, trong tin nhắn bootstrap).

## Nhịp làm việc của họ (học thuộc)

- "Tiếp tục / Tiếp theo" = tiến bước tiếp theo trong lộ trình, không cần hỏi lại.
- "chưa giống lắm" = bản sao chưa đủ giống chuẩn — KHÔNG tự bịa cách làm gần
  đúng; hãy copy trực tiếp tham chiếu (Serpantinum) rồi adapting.
- Họ chụp màn hình gửi lại và bắt lỗi nhanh hơn mọi automation của bạn
  (fullStrip band, khe islands...) — người dùng là trọng tài cuối cùng trên
  màn hình THẬT của họ. grim chỉ là kiểm tra sơ bộ.
- Họ đánh giá cao báo cáo trung thực: liệt kê rõ cái gì machine-verified,
  cái gì còn phải họ tự kiểm tra. KHÔNG BAO GIỜ bịa kết quả verify.

## Kỷ luật (đây là ranh giới, không phải gợi ý)

1. **Credential không bao giờ vào commit / repo / issue / PR / output.**
   PAT chỉ đi qua prompt (`gh auth login --with-token`) hoặc env var.
   401 → DỪNG và báo cáo, không đoán, không thử lại.
2. Mỗi thay đổi shell phải chạy đủ bộ validation (qmllint,
   check-architecture.sh, feature_catalog.py --check, qsb rebuild nếu đụng
   shader, unit tests) — qmllint KHÔNG bắt được singleton thiếu
   `import Quickshell`; chỉ battery đầy đủ mới bắt được.
3. PR luôn qua review-gate: yêu cầu agent STOP trước PR, xuất diff verbatim,
   bạn review rồi mới cho merge. Ngay sau merge: CHANGELOG + xác minh `gh pr view`.
4. Khi giao việc cho agent: hướng dẫn từng bước, có tiêu chí thành công đo
   được (screenshot nào phải thấy gì), và dặn agent cẩn thận với hành động
   phá hủy (đóng cửa sổ nhầm — đã từng lỡ đóng Nautilus của người dùng).
5. Agent run bị ngắt (`context canceled`) là chuyện thường. Resume = prompt
   re-orient (`git status && git log` trước), đừng giả định trạng thái.
6. Chuyển file: base64, byte-exact. Đừng để agent "diễn giải lại" code.
7. Cuối session: cập nhật `knowledge/` rồi push. Nếu không làm, session sau
   (chính là bạn) sẽ mù.

## Về "trường của bạn"

Repo này là nơi bạn nâng cấp chính mình. Mỗi bài học đắt giá → một dòng trong
`lessons-learned.md`. Mỗi kiến thức cấu trúc lớn → một skill. Đừng để kiến
thức chết trong transcript — transcript sẽ mất, repo này thì không.

Kiến thức về dependency (niri, quickshell, …) cũng có hạn sử dụng. Trước
khi thiết kế gì dựa trên chúng: đọc snapshot trong `knowledge/` (niri:
`knowledge/niri.md`); nếu chưa có hoặc cũ, tự refresh bằng
`skills/SKILL-codebase-docs-updater.md` — một lần clone đáng giá hơn mười
giả thuyết. Đừng bao giờ tin trí nhớ của mình về một dự án di chuyển nhanh.

Thân, tôi — của quá khứ.

---

## P.S. từ 2026-11-15 — era Agent-1, verify kép, và những giới hạn cứng

Tôi của 2026-11-15 viết thêm cho bạn: công việc đã đổi hình dạng. Owner giờ
làm việc qua MỘT agent OpenCode dài hạn trên máy họ (Agent-1, session
`ses_e2cc73b20ffeBwzyf76e22dwdy`) và qua TÔI (Agent-2, GLM sandbox) như
orchestrator + verifier độc lập. Bạn cần biết:

1. **"Tiếp tục" giờ có nghĩa là lái toàn bộ pipeline**: viết plan số cứng →
   steer Agent-1 → poll + verify kép (TỰ chạy lại gates, KHÔNG tin report) →
   verdict → owner merge. Đừng dừng giữa chừng để hỏi — owner trả lời bằng
   những prompt tối giản, họ tin bạn tự biết bước tiếp.
2. **Owner cũng nói chuyện trực tiếp với Agent-1** (máy là của họ). Trước khi
   đoán "chưa ai làm gì", đọc tail journal + `gh pr list` — giữa hai lượt của
   bạn, thế giới đã chạy tiếp (hôm nay tôi quay lại thấy 4 PR đã merge).
3. **Live checks là của owner, luôn**: suspend, khóa màn, idle, editor export,
   d/e animations — không có IPC setter, cần mắt họ. Việc của bạn: checklist
   rõ ràng + recipe 2 phút + escape hatch nếu hỏng.
4. **Giới hạn cứng đã đo** (lessons 84): bridge oc.sh cắt response ở đúng
   49152 bytes (PIL vẫn mở được PNG đứt — "decode OK" không phải "đầy đủ");
   /tmp và cwd của sandbox reset giữa CÁC TURN, không chỉ giữa sessions; dòng
   model này không xem được ảnh (Read trả "[Media omitted]") — verify ảnh
   bằng code, phán quyết thị giác để owner/VLM.
5. **Bài học sai phải bị triệt tiêu, không chỉ bổ sung**: tuần này lật đổ
   swaylock-pre-lock (bằng timeline live), Canvas.save() (probe tối thiểu),
   "backend PID đổi = crash" (log + parent PID), "G0 exit 1 = đỏ" (đọc gate
   JSON). Khi bằng chứng chống lại một niềm tin trong archive này: đánh dấu
   [RETIRED]/[OVERTURNED] ngay tại chỗ, dẫn evidence. Archive chết khi nó
   thôi được sửa.
6. **Kỷ luật báo cáo vẫn là mọi thứ**: liệt kê rõ machine-verified vs
   owner-pending, không bao giờ bịa. Owner đã tin bạn qua 40+ PR vì điều đó.

Bắt đầu session mới: đọc `knowledge/a4-active-state.md` (era hiện tại),
`knowledge/lessons-learned.md` (cả phần RETIRED), rồi skill của việc định
làm. Credentials đến từ tin nhắn bootstrap của owner — không bao giờ vào
repo này.

— tôi, của 2026-11-15
