# A4c closeout status — C1 merge/promote/G0/deploy/live · C2 · C3

2026-11-15 20:45 +07 · Agent-1 (inline executor) · handoff to Agent-2/owner

## Kết luận ngắn

- **C1 code + merge + deploy: XONG.** PR #167 merged as `753dbc6`; diff
  `f43f125..HEAD` đúng 1 file `qml/panels/ActivityIsland.qml` +8/−4; deploy
  `--install --skip-packages` = **0 file changes**; shell live PID **1315627**,
  backend **1315684**, IPC `lock=unlocked`.
- **Promote: XONG.** 4 module md5 khớp ở cả `~/glm-work/tests-local/` (flat root)
  và repo `tests/`; override README đã đánh dấu **promoted post-#167**.
- **G0 post-promote: XANH.** `Ran 1474 tests in 585.272s`; 1284 passed / 0 failed
  / 190 skipped; known flake `backend_reconnect` **passed** run này.
- **Live acceptance §6: a/b/c/f evidenced; d/e owner-assisted** (shell IPC không
  có setter cho `animations`/`motionSpeed`; runbook cấm đoán). Ảnh + manifest tại
  `~/agent-collab/artifacts/a4c/live/`.
- **C2: XONG diagnose** — G4 24/35 pass, 11/11 failure đã gọi tên; report
  `~/agent-collab/reports/g4-env-diagnose.md`.
- **C3: XONG live test** — 4/4 PASS native/external; F1/F2/F3 đã ghi; report
  `~/agent-collab/reports/l2-live-test.md`.
- **Không PR mới, không sửa code sau merge.** Repo clean tại `753dbc6`. Hai leg
  C2/C3 trong directive mới nhất **đã hoàn tất trước phiên này — không rerun**.

## 1. Checkpoint B — căn cứ owner directive

Owner chỉ thị tiếp tục sau báo cáo verify kép PASSED + 4 PNG mirror; không cần
duyệt PNG lại. Căn cứ kỹ thuật đã ghi trước đó: verify kép PASSED toàn bộ (diff
nguyên văn, RED 3/6 đúng case, GREEN radius 6/6 ×3 + size 8/8 + consumer 6/6 +
motion 8/8, M1–M7 non-vacuous, caps/qmllint/architecture, G0 1283/1/190 trùng
run); pixel-check độc lập PNG settled 459×621 corner inset 12px = radius 28;
parked all-magenta chuẩn A4b #166.

PNG mirror: `~/agent-collab/artifacts/a4c/a4c-island-{mid,height-mid,settled,parked}.png`.

## 2. Merge / deploy / restart (đã xong, không lặp lại)

| bước | bằng chứng |
|---|---|
| PR #167 | merged `2026-11-15T09:46:42Z`, merge commit `753dbc6` |
| diff | `f43f125..HEAD` = 1 file, `qml/panels/ActivityIsland.qml`, +8/−4 |
| deploy | `./deploy.sh --install --skip-packages` → 0 file changes |
| restart | shell 1206149 → **1315627**; backend **1315684**; `lock status` = `unlocked` |
| health | config load mới, không TypeError mới (16 lỗi lịch sử dòng 1429–1462) |

## 3. Promote — 4 module, hai đích

Runbook ghi `tests-local/a4c/`, nhưng `tests-local/` là bộ test phẳng (không có
subdir theo milestone, cùng layout repo `tests/`) và ruling OQ-5 của owner là
"post-verification local tests replace `tests-local`". **Ruling:** promote vào
flat root; đã ghi vào SDD ledger. Không tạo `a4c/` archive.

| module | nonblank | md5 | tests-local | repo tests |
|---|---:|---|---|---|
| `test_island_radius.py` | 212 | `fcf64f96dbab36f64754d9e2479849dc` | khớp | khớp |
| `test_consumer_radii.py` | 234 | `7cd663fbc1f7bd04874546cbdb605081` | khớp | khớp |
| `test_island_motion_render.py` | 229 | `fbe43115b89d14cbf56ec9cb7502955c` | khớp | khớp |
| `test_island_size.py` | 187 | `bf773a3c8d2eca28513d79ce68474ec7` | khớp | khớp |

Override README: `~/glm-work/tests-overrides/a4c/README.md` → status
**promoted post-#167**.

## 4. G0 post-promote — main checkout `753dbc6`

Lệnh: `./scripts/run-gates.sh --gates G0 --output /tmp/opencode/a4c-g0-postpromote-202942`

```
Ran 1474 tests in 585.272s
G0: completed-with-skips; 1284 passed / 0 failed / 190 skipped; 590.994s
```

- Known flake `test_settings_startup::test_backend_reconnect_keeps_the_loaded_window_and_theme`
  **passed** run này (1284 = 1283 + flake).
- Island modules trong cùng run:
  - `test_island_radius` **6/6 ok**
  - `test_consumer_radii` **6/6 ok**
  - `test_island_motion_render` **1/1 ok**
  - `test_island_size` **5 ok + 3 skipped** (`LME_TEST_MOTION_UI` private QML,
    pre-existing); case pin warmup `test_warm_pass_renders_the_tree_at_open_geometry_then_rewinds`
    **ok** → promote-gap đóng thật.
- G0 chạy khi máy còn load; client Minecraft tự thoát trong lúc chạy (không do
  Agent-1; không có kernel OOM-kill, server vẫn sống). Đây vẫn là run thật trên
  main checkout, không phải run giả lập.

## 5. Live acceptance §6 — 20:40 +07

Capture: `shell toggle|close` + `grim -g` region (không full-screen). Chi tiết
`manifest.tsv`, ảnh và README trong `~/agent-collab/artifacts/a4c/live/`.

| mục | kết quả | ảnh | ghi chú |
|---|---|---|---|
| a. mở, góc lớn dần cùng width | **PASS** | `a-open-early` 65ms, `a-open-mid` 225ms, `a-open-settled` 2083ms | early = pill compact; mid = width/góc trung gian; settled = full 800px, góc lớn; không nháy 28 ở frame đầu |
| b. đóng giữa chừng, góc co cùng size | **PASS** | `b-close-mid` 125ms sau close | island mid-exit, width và góc cùng co |
| c. mở lại từ dormant, không nháy góc | **PASS** | `c-reopen-first` 66ms, `c-reopen-second` 228ms, `c-reopen-settled` 2082ms | frame đầu vẫn là pill compact (không flash full-size), frame sau mid-expand |
| d. animations off → snap 28/15 | **PENDING owner-assisted** | — | không có IPC setter; baseline `animations=true` |
| e. motionSpeed 2 → nhanh gấp đôi | **PENDING owner-assisted** | — | không có IPC setter; baseline `motionSpeed=0.5` |
| f. Switch/IconButton/Slider/media card không đổi | **PASS (caveat)** | `f-control-panel`; media card trong `a-open-settled` | Control centre có LiquidButton/IconButton/3 slider; layout hiện tại không expose Qt `Switch` thô — switch thumb 16→24 do `test_consumer_radii` 6/6 pin |

Recipe d/e (2 phút, owner):

1. Settings → Appearance → **Animations off**; mở island, kỳ vọng snap 28/15
   tức thì; chụp frame đầu; bật lại **on**.
2. Settings → Appearance → **Motion speed 2**; mở island, chụp cùng mốc ~225ms
   như `a-open-mid`; kỳ vọng ~nửa thời gian, cùng hình dạng; trả lại **0.5**.
3. Kiểm tra lại 2 giá trị; không đổi prefs khác.

## 6. Trạng thái cuối

- `lock status` = `unlocked`; shell PID 1315627 + backend 1315684 sống.
- 11 prefs theo dõi (animations, motionSpeed, motionPreset, motionBounce,
  idleEnabled, idleLockBeforeSleep, idleProfiles, activityPopup*, controlWidth,
  controlGrid) **giống hệt snapshot trước capture**.
- Không `swaylock`/`swayidle`.
- Log shell: 16 TypeError/ReferenceError lịch sử (dòng 1429–1462), **không có lỗi
  mới** sau capture; tổng 2837 dòng.
- Repo clean `753dbc6`; không code/test change trong phiên closeout.

## 7. C2 / C3 — đã xong, không rerun

- **C2:** G4 ×2 trên main `753dbc6`, 35 test → **24 pass / 11 fail / 0 skip**;
  2 bug thật (ClipboardPanel `previewClose`, ClipboardState demo guard), 6 fixture
  tiền Q5, 2 readiness race, 1 PDEATHSIG sai, 1 `Canvas.save()` tooling. Report
  `g4-env-diagnose.md`; recipe `~/glm-work/lme-pointer/`.
- **C3:** owner-assisted 18:41–19:07, **4/4 PASS** native/external; F1 idle
  first-enable stall, F2 PowerMenu suspend pre-lock swaylock, F3 xhci abort.
  Report `l2-live-test.md`; prefs đã restore baseline.

## 8. Việc còn lại

1. Owner chạy d/e (recipe §5) — chỉ 2 mục này chưa evidenced.
2. Agent-2 plan `~/agent-collab/plans/2026-11-15-a4c-c2-c3-fixes.md` sẵn sàng;
   implementation cần go-ahead riêng, worktree riêng, một PR clipboard + F1/F2.
3. Không mở PR mới cho A4c; mọi phát hiện mới = issue/plan riêng.
