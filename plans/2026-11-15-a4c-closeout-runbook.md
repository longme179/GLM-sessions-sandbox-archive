# A4c closeout runbook — C1 merge/deploy/live → C2 G4 → C3 L2
(Agent-2 lập kế hoạch + orchestrate · Agent-1 thực thi · 2026-11-15)

Owner chỉ thị sau báo cáo verify kép PASSED + 4 PNG mirror: "tiếp tục làm việc với
Agent-1, Agent-2 lập kế hoạch + orchestrate" ⇒ **Checkpoint B ĐÃ THÔNG QUA theo
chỉ thị owner**. Căn cứ kỹ thuật thay mặt: verify kép PASSED toàn bộ (diff nguyên
văn, RED/GREEN ×3, M1-M7, caps/qmllint/architecture, G0 1283/1/190 trùng run),
pixel-check độc lập PNG (settled 459×621 corner inset 12px = radius 28; parked
all-magenta chuẩn pattern A4b #166), promote-gap đã đóng (override đủ 4 module,
PR body cập nhật). PNG: `~/agent-collab/artifacts/a4c/` + mirror
`download/a4c_polish/pngs/`. Journal phải ghi rõ căn cứ này.

## Leg 1 — C1 closeout (thứ tự bắt buộc, evidence sau mỗi bước)

1. **Merge:** `gh pr merge 167 --merge` (merge-commit theo convention #166).
   Verify: `git -C ~/lme-fedora-niri-qs log --oneline -2`; `git diff f43f125..HEAD --stat`
   phải ra đúng 1 file `qml/panels/ActivityIsland.qml` +8/−4; `git pull --ff-only`.
2. **Promote ĐỦ 4 module** (md5 phải khớp ở CẢ HAI đích `tests-local/a4c/` + repo `tests/`):
   `test_island_radius.py fcf64f96…` · `test_consumer_radii.py 7cd663fb…` ·
   `test_island_motion_render.py fbe43115…` · `test_island_size.py bf773a3c…`.
   README override đánh dấu "promoted post-#167".
3. **G0 post-promote** (main checkout, isolated run-gates): kỳ vọng `Ran 1474 tests`,
   0 fail (chấp duy nhất `backend_reconnect` nếu reproduce). **CHỐT bắt buộc:**
   `test_island_size` 8/8 + `test_island_radius` 6/6 + `test_consumer_radii` 6/6
   XANH trên main-sau-merge = chứng minh promote-gap đóng. Ghi G0 line vào journal.
4. **Deploy:** `./deploy.sh --install --skip-packages` từ main checkout.
5. **Restart shell live** theo procedure chuẩn các phase trước: track PID mới
   (shell + backend), IPC lock `unlocked`, chờ healthy (mở/đóng 1 panel qua IPC).
   KHÔNG đụng prefs của owner.
6. **Live acceptance 6 mục §6 — tự evidence hóa qua IPC + grim + qslog:**
   a. Mở island: góc bo lớn dần cùng width, KHÔNG nhảy 28 — 2 ảnh grim mid
      (cách ~100ms) + 1 ảnh settled.
   b. Đóng giữa chừng (open + ESC ngay): góc co cùng size — 1 ảnh mid-close.
   c. Mở lại từ dormant (đóng hẳn, chờ dormant rồi mở lại): không nháy corner —
      2 ảnh đầu liên tiếp.
   d. Animations off (pref): snap tức thì 28/15 — ảnh ngay frame đầu.
   e. motionSpeed 2: nhanh gấp đôi, cùng hình dạng — ảnh mid cùng mốc thời gian
      của (a) để đối chiếu.
   f. Switch/IconButton/Slider/media card KHÔNG đổi — 1 ảnh panel chứa switch +
      button (đối chiếu static pin đã xanh).
   Evidence → `~/agent-collab/artifacts/a4c/live/` + journal.
   **RESTORE prefs** (animations/motionSpeed) về đúng giá trị đọc được TRƯỚC khi
   đổi; nếu không đọc/ghi được qua IPC thì mục d/e chuyển owner-assisted (ghi rõ),
   không đoán.
7. **Journal C1 đóng** + steer Agent-2 (kèm G0 line, PID mới, kết quả 6 mục).

## Leg 2 — C2 G4 diagnose + LME_TEST_POINTER (per plan §9, KHÔNG PR)

Đủ 5 bước đúng nguyên văn §9: inventory env 4 module G4 + helper signatures →
`command -v` deps (KHÔNG cài package chưa owner duyệt) → `~/glm-work/lme-pointer/`
wrapper swaymsg (đọc SWAYSOCK từ env test truyền) + **verify helper THẬT bằng QML
click counter trong sway headless** → chạy G4 `--env-file` + `--pointer-dir` →
report `~/agent-collab/reports/g4-env-diagnose.md` + journal. Tiêu chí đóng: G4
xanh HOẶC mọi skip gọi tên tool thiếu + owner biết; recipe tái sử dụng cho G1-G3.
An toàn: disposables của run-gates, không đụng shell live.

## Leg 3 — C3 L2 live test (per plan §10 — owner-assisted)

Agent-1 **CHỈ PREP**: checklist 4 mục, IdlePage timeout 1 phút + plan restore,
2 escape hatch mở sẵn (keybind → swaylock fallback + demo escape hatch),
`journalctl --user -f` theo dõi, template config diff trước/sau, timeline
`lock status`. **KHÔNG suspend tự động — chờ owner xếp buổi** (owner tại máy,
buổi ngày). Fail nào: ghi bằng chứng, KHÔNG fix-forward (issue/plan riêng).
Report `~/agent-collab/reports/l2-live-test.md` sau buổi test.

## Giới hạn toàn cục

- Không PR mới ngoài #167; không sửa code sau merge (phát hiện vấn đề = issue/plan mới).
- Shell live: chỉ deploy + restart + evidence; mọi prefs owner phải restore.
- Mọi số trong journal phải từ lệnh thật đã chạy (convention từ A4a).
- Thứ tự đóng: C1 (merge+deploy+live 6 mục) ⇒ C2 report ⇒ C3 prep+owner window ⇒
  journal tổng kết Tier A "G4 env diagnose + LME_TEST_POINTER, L2 live test" XONG.
