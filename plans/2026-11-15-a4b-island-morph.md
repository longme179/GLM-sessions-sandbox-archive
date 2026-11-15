# Plan: A4b — Wire ActivityIsland vào pill motion language (MotionValue morph mode)

**Ngày:** 2026-11-15 · **Tác giả:** Agent-2 (Tier A, mục A4 leg b) · **Verify kép:** Agent-1
**Branch:** `feat/island-morph` từ `main @ 165a72f` (sau #165) · **Repo:** `longme179/lme-fedora-niri-qs` (AGPL-3.0-or-later)
**Đây là PR đầu tiên của A4 có thay đổi animation NHÌN THẤY ĐƯỢC** ⇒ plan số cứng + render seam (sway+grim real pixel) + live acceptance như #163.
**Chống code ảo giác:** engine cases đọc giá trị THẬT của MotionValue/island theo thời gian thực (run_qml offscreen, animation clock thật) + render case chụp pixel thật giữa chuyến morph; RED trên main trước GREEN; 2 mutation probe chứng minh test không rỗng; Agent-1 chạy lại toàn bộ trên máy mình.

---

## 0. Bối cảnh + quyết định đã chốt (số cứng — KHÔNG đổi khi implement)

### 0.1 Hiện trạng (main @ 165a72f)

`qml/panels/ActivityIsland.qml` (65 nonblank) đã có 2 MotionValue:
```qml
width:  Math.max(1, Math.min(expandedWidth,  Theme.springMotion ? widthSpring.value  : compactWidth + (expandedWidth - compactWidth) * expansion))
height: Math.max(1, Math.min(expandedHeight, Theme.springMotion ? heightSpring.value : 30 + (expandedHeight - 30) * expansion))
MotionValue { id: widthSpring;  large: true; value: root.compactWidth; target: root.mounted && (root.shown || root.warmupActive) ? root.expandedWidth  : root.compactWidth }
MotionValue { id: heightSpring; large: true; value: 30;               target: root.mounted && (root.shown || root.warmupActive) ? root.expandedHeight : 30 }
```
`qml/components/MotionValue.qml` (16 nonblank) = SpringMotion bọc `Theme.springStiffness/Damping` (stiffness 560 cho large, damping ratio .783 expressive ⇒ spring **overshoot ~1.9%** ≈ 9px trên 460, settle ~540ms theo epsilon .02). MotionValue fan-in **8** consumer: ControlDashboard, ActivityIsland, MotionPopup, ExpressiveSwitch, IconButton, StretchIndicator, LiquidSlider, LiquidButton.

### 0.2 Thiết kế A4b (opt-in morph mode — 7 consumer kia KHÔNG đổi)

**Nguyên tắc:** morph mode là **opt-in** bằng property mới `morphMs` (default 0 = spring nguyên vẹn, hành vi byte-for-byte như cũ cho 7 consumer còn lại). Island là consumer đầu tiên bật mode này với token của A4a:

| Chủ thể | Token | Nghĩa |
|---|---|---|
| `widthSpring` | `morphMs: Motion.morph` | 420ms/speed — width morph theo curve lỏng |
| `heightSpring` | `morphMs: Motion.shapeshift` | 820ms/speed — height nở chậm, đuôi dài |
| Cả hai | `morphCurve` default `[0.16, 1, 0.3, 1, 1, 1]` + `Easing.BezierSpline` | cubic-bezier(0.16,1,0.3,1) — iNiR "liquid morph" |

**Cơ chế:** `onTargetChanged` dispatch — morphMs > 0 → `morphRetarget()` (NumberAnimation standalone target chính object, from = value hiện tại ⇒ đảo chiều giữa chuyến bay thì restart từ chỗ đang bay, đúng yêu cầu comment dòng 38-43 của ActivityIsland); morphMs = 0 → `retarget()` spring như cũ. `snapTo` bị shadow: 3 phép gán y hệt SpringMotion + `morphAnimator.stop()` (warm-up pass và dormant park vẫn snap tức thì như hôm nay). `enabled: morphMs > 0 ? Theme.animations : Theme.springMotion`.

**Probe 0a đã chạy trên máy fedora (2026-11-15, offscreen quickshell):** NumberAnimation standalone trong QtObject animate property của chính object — CHẠY. Samples thật: 30ms→41% (lý thuyết y=0.407 ✓), ~210ms→95%, settle đúng ~420ms, **không overshoot**. Fallback (nếu regression nào đó break): tự tính bezier y=3t−3t²+t³, x(t)=0.48t−0.06t²+0.58t³ trong FrameAnimation driver — KHÔNG dùng nếu không cần.

### 0.3 Số học curve (đã hiệu chỉnh bằng probe — mọi window test dựa trên đây)

Với y-threshold, thời điểm đạt (phần D = duration):
| Threshold | t param | x(t) = T/D | Tính ra |
|---|---|---|---|
| y = 0.805 | 0.42 | 0.234 | 23.4%·D |
| y = 0.953 | 0.64 | 0.4286 | 42.9%·D |
| y = 0.9989 (=459.5/460) | 0.80 | 0.800 | **80%·D** |
| y = 1.0 | 1.0 | 1.0 | 100%·D |

⇒ **Window "first-reach"** (engine, sampler 25-30ms):
- morph 420, đích 460, ngưỡng 459.5: T = 336ms ⇒ window **[320, 400]**
- shapeshift 820, d=500 (30→530), ngưỡng 529.5: T = 656ms ⇒ window **[630, 730]**
- motionSpeed 2 (morph=210), ngưỡng 459.5: T = 168ms ⇒ window **[150, 220]**
- island width (459.5): **[320, 400]**; island height (E−0.5): **[630, 730]**

Spring (main, sẽ RED): vượt 459.5 từ ~125ms và overshoot tới ~469 ở ~214ms ⇒ mọi window trên fail trên main.

### 0.4 Hành vi thay đổi phải công khai (behavior change — owner phải biết)

1. **springMotion=false:** hôm nay island size morph theo `expansion` (spatialCurve, jelly preset overshoot); sau A4b = token morph (morphCurve, không bao giờ vượt). Lý do: size morph của island giờ là một phần pill motion language (mục tiêu A4); `springMotion` vẫn điều khiển flight (SlideLoader) + mọi spring khác. Test pin: tắt springMotion ⇒ island vẫn morph 420/820 đúng curve.
2. **animations=false:** Motion.morph/shapeshift = 0 ⇒ morphMs = 0 ⇒ nhánh spring + effectiveReducedMotion ⇒ snapTo tức thì. Đúng hợp đồng token A4a (case test riêng).
3. Overshoot thô của spring value (raw) biến mất — bezier y ≤ 1 luôn.

### 0.5 Giới hạn.RENDER test không RED trên main qua pixel-timing (spring bị clamp bởi binding min(expandedWidth,…) nên pixel cũng không vượt) — RED của PR này nằm ở **engine + static** ("Unable to assign to non-existent property morphMs" + window sai + wiring thiếu). Render test là seam MỚI: chứng minh pixel thật giữa chuyến morph khớp geometry QML báo (±8px), đúng tinh thần #161/#163 (renderer-level illusion chỉ render test bắt được).

---

## 1. File chính xác

| File | Hành động | Nonblank | Ghi chú |
|---|---|---|---|
| `qml/components/MotionValue.qml` | **sửa** | 16 → ~38 (cap 250, không vào largeFiles) | opt-in morph mode |
| `qml/panels/ActivityIsland.qml` | **sửa** | 65 → 66 (cap 250) | wire 2 token, bỏ ternary springMotion ở width/height |
| `~/glm-work/tests-overrides/a4b/test_island_motion.py` | **tạo (override)** | ~170-210 (cap 250) | 6 case engine + static; KHÔNG commit (tests/ gitignored) |
| `~/glm-work/tests-overrides/a4b/test_island_motion_render.py` | **tạo (override)** | ~150-190 (cap 250) | 1 case render seam sway+grim |
| `~/glm-work/tests-overrides/a4b/README.md` | tạo | — | scope + md5 |

`git diff --stat origin/main` cuối cùng **chỉ được có 2 file** (MotionValue.qml, ActivityIsland.qml). KHÔNG đụng: Theme.qml (253 pin), Motion.qml (25 pin), SpringMotion.qml, SlideLoader.qml, qmldir, THIRD_PARTY.md (credit PillMotion đã có từ A4a), schema/preferences, 7 consumer còn lại của MotionValue.

**Nội dung mới `qml/components/MotionValue.qml` (nguyên văn):**

```qml
// SPDX-License-Identifier: AGPL-3.0-or-later
// Role: MotionValue.qml (shared layer, fan-in 8).
// Shared component/helper; keep API stable for wide QML reuse.
import QtQuick
import "../theme"

SpringMotion {
    id: root
    property bool large: false
    property real response: 1
    // Opt-in pill-family size morph (A4b): morphMs > 0 replaces the physics
    // spring with a token-timed bezier flight along morphCurve. 0 keeps the
    // spring every other consumer rides, so the default changes nothing.
    property int morphMs: 0
    property var morphCurve: [0.16, 1, 0.3, 1, 1, 1]
    enabled: morphMs > 0 ? Theme.animations : Theme.springMotion
    stiffness: Theme.springStiffness(large) * response * response
    damping: Theme.springDamping(large) * response
    positionEpsilon: .02
    velocityEpsilon: .02
    // A standalone animation targets this object's own value; from/to are set
    // imperatively so a reversal restarts from wherever the flight is now.
    property NumberAnimation morphAnimator: NumberAnimation {
        target: root; property: "value"; duration: Math.max(0, root.morphMs)
        easing.type: Easing.BezierSpline
        easing.bezierCurve: root.morphCurve
    }
    onTargetChanged: morphMs > 0 ? morphRetarget(target) : retarget(target)
    function morphRetarget(v) {
        morphAnimator.stop()
        if (target !== v) target = v
        morphAnimator.from = value
        morphAnimator.to = v
        morphAnimator.restart()
    }
    // Shadows SpringMotion.snapTo: same three writes, plus retiring a morph
    // flight mid-air (warm-up passes and dormant parks snap on purpose).
    function snapTo(v) {
        morphAnimator.stop()
        value = v; velocity = 0; _running = false
    }
    Component.onCompleted: snapTo(target)
}
```

**Sửa `qml/panels/ActivityIsland.qml` (đúng 4 chỗ):**
1. Dòng 28 → `    width: Math.max(1, Math.min(expandedWidth, widthSpring.value))`
2. Dòng 29 → `    height: Math.max(1, Math.min(expandedHeight, heightSpring.value))`
3. Trước 2 MotionValue thêm comment 1 dòng: `    // The pill family's motion language (A4b): width rides the morph token, height the long shapeshift tail.`
4. Dòng 34 → `    MotionValue { id: widthSpring; large: true; morphMs: Motion.morph; value: root.compactWidth; target: root.mounted && (root.shown || root.warmupActive) ? root.expandedWidth : root.compactWidth }`
5. Dòng 35 → `    MotionValue { id: heightSpring; large: true; morphMs: Motion.shapeshift; value: 30; target: root.mounted && (root.shown || root.warmupActive) ? root.expandedHeight : 30 }`

Tất cả handler còn lại (onDormantChanged, onWarmupActiveChanged snapTo, x/y, radius `15 + 13 * expansion`) **giữ nguyên**.

---

## 2. Test contracts (exact)

### 2a. Engine + static — `test_island_motion.py` (8 case: 6 engine + 2 static)

Header theo pattern `test_motion_tokens.py`: `import test_local_qml as qml_tests`; REPO = parents[1]. Engine cases dùng `run_qml('import "qml/components"\nimport "qml/theme"\nimport "qml/services"', body)` (island case thêm `import "qml/panels"`); body theo pattern phase Timer của test_media_ambient: set prefs qua `ShellState.snapshot = Object.assign(...)`; sampler Timer 25-30ms ghi `{t: Date.now()-t0, v: ...}` vào mảng, finish(mảng) đúng 1 lần.

**Case 1 — `test_morph_value_flies_the_token_curve_without_overshoot`** (MotionValue trực tiếp, `morphMs: 420; value: 0; target: 0`, flip target=460 tại tick đầu):
- moving: sample t∈[55,95]ms có v ∈ [230, 445] (bezier lý thuyết 295-366; snap-broken = 460 → fail trần; dead = 0 → fail sàn);
- **no-overshoot: mọi sample t∈[150, 450] ≤ 460.5** (spring main peak ~469 @ ~214ms → RED);
- first-reach 459.5 ∈ **[320, 400]** (spring main ~125ms → RED);
- settled: sample cuối (t≈700) v == 460 ± 0.02.

**Case 2 — `test_shapeshift_pace_is_the_long_tail`** (`morphMs: 820; value: 30`, flip target=530):
- moving: t∈[100,160] v ∈ [280, 440] (lý thuyết 343-399);
- mid-cap: mọi sample t∈[280, 350] ≤ 515 (bezier ≤ 507; spring settled 530 → RED);
- first-reach 529.5 ∈ **[630, 730]** (spring ~150ms → RED);
- settled 530 ± 0.02; no-overshoot ≤ 530.5 trong [100, 900].

**Case 3 — `test_animations_gate_collapses_the_morph_instantly`** (prefs `{animations: false, motionSpeed: 1}`; MotionValue `morphMs: Motion.morph` — evaluate 0): flip target=300 ⇒ tick kế (+50ms) v == 300 **chính xác**, tick sau vẫn 300; đồng thời result chứa `motionMorph == 0` (pin token collapse ở mép consumer).

**Case 4 — `test_motion_speed_divides_the_island_tokens`** (prefs `{animations: true, motionSpeed: 2}`; `morphMs: Motion.morph` = 210): flip target=460:
- result chứa `motionMorph == 210`;
- first-reach 459.5 ∈ **[150, 220]** (mutation hardcode 420 → 336 → FAIL).

**Case 5 — `test_island_wires_the_pill_morph_language`** (island thật trong `FloatingWindow { fullscreen: true }`, host = contentItem; prefs `{animations: true, motionSpeed: 1}`; `ShellState.activityAnchorWidth = 120`; mở = `ShellState.activityOpen = true`; sampler 30ms đến t>1600, đóng, sampled đến t_close>1200):
- `expandedW == 460 ± 1` (deterministic: min(460, host−28));
- `E` (expandedHeight đo được) ≥ 200 (sanity content load);
- first w ≥ 459.5 ∈ **[320, 400]** (main-spring ~125ms → RED);
- first h ≥ E−0.5 ∈ **[630, 730]** (main ~130ms → RED);
- mid-flight: tồn tại sample t∈[90, 200] với w ≤ 448 (bắt wiring-dead/instant);
- bound: max(w) ≤ 461, max(h) ≤ E+1;
- close: tồn tại sample t_close∈[60, 350] với w ∈ (125, 400) (morph đảo chiều, không snap); cuối cùng w == 120 ± 1, h == 30 ± 1 (dormant snap);
- static pin (đọc file): ActivityIsland.qml chứa `morphMs: Motion.morph` và `morphMs: Motion.shapeshift`; 2 dòng width/height **không** chứa `springMotion`; MotionValue.qml chứa `property int morphMs: 0` và `Easing.BezierSpline`; tập file trong `qml/` chứa "morphMs" == chính xác {MotionValue.qml, ActivityIsland.qml}.

**Case 6 — `test_snap_retires_a_morph_flight_and_legacy_consumers_stay_springs`** (morphMs 420, flip 460, tại ~150ms gọi `snapTo(137)`):
- 2 sample kế tiếp v == 137 chính xác và đứng yên (shadow thiếu stop() ⇒ animator tiếp tục ghi value ⇒ drift → FAIL);
- static: 7 file consumer (ControlDashboard, MotionPopup, ExpressiveSwitch, IconButton, StretchIndicator, LiquidSlider, LiquidButton) **không** chứa "morphMs" (pin opt-in an toàn).

**RED dự kiến trên main:** 6/6 fail — engine cases: quickshell load fail, log chứa `Unable to assign to non-existent property "morphMs"` (run_qml assert NotIn "Unable to assign" bắt); case 5/6 static fail vì wiring/property chưa tồn tại. Nếu có failure ngoài dự kiến → DỪNG, báo Agent-1.

**Mutation probes bắt buộc sau GREEN:**
- **M1 (spring-revert):** dòng dispatch đổi thành `onTargetChanged: retarget(target)` → case 1 FAIL (overshoot 469 > 460.5), case 2 FAIL (530 > 515), case 4/5 FAIL (reach sai window); revert → GREEN.
- **M2 (hardcode duration):** `duration: 420` literal trong morphAnimator → case 2 FAIL (reach 336 ∉ [630,730]), case 4 FAIL (reach 336 ∉ [150,220]); revert → GREEN.

### 2b. Render seam — `test_island_motion_render.py` (1 case, pattern #161/#163)

Fixture: sway headless (WLR_BACKENDS=headless, pixman) + quickshell wayland; entry: `FloatingWindow { fullscreen: true; color: "#ff00ff" }` chứa `ActivityIsland {}` (host = window). Marker:
- `RENDER_ISLAND_HOST <w> <h>` lúc khởi động;
- Timer 600ms: `ShellState.activityOpen = true` + log `RENDER_ISLAND_OPEN`;
- logger Timer 30ms: `RENDER_ISLAND_GEOM <t> <w> <h>` (t = ms kể từ open);
- Timer 2400ms: `ShellState.activityOpen = false` (đóng tự động);
- banned strings: ReferenceError/TypeError/Unable to assign/Binding loop.

Python chụp grim theo mốc elapsed-sau-OPEN (đọc log polling): **mid ≈ 160ms** (retry nguyên lượt mở nếu GEOM line khớp nằm ngoài [120, 220] — tối đa 3 lần), settled ≈ 1500ms, close-mid ≈ 2600ms, parked ≈ 3600ms. Assert:
1. **mid:** GEOM khớp có w ∈ [400, 452] (main-spring = 460 clamp từ ~140ms → RED qua geometry window) và pixel đo (scan run liền kề trên hàng tâm) ≈ w ± 8;
2. **settled:** logged w == 460 ± 2; pixel đo ≈ logged w/h ± 5;
3. **monotone:** các capture mở tăng dần ± 4, không vượt 463 / E+3;
4. **close-mid:** logged w ∈ (125, 400) (đang thu nhỏ);
5. **parked:** hàng tâm tại vị trí island = magenta thuần (island đã park ngoài viewport);
6. giữ lại PNG (mid/settled/close) khi `A4B_KEEP_PNGS` trỏ thư mục — artifacts cho owner duyệt ảnh.

**Pixel-probe TRƯỚC khi chốt render test** (Task 4a): đo (i) grim latency ×5, (ii) island body có detect được trên nền magenta phẳng không (GlassPanel fill/border/content). Nếu fill liquid quá mờ: fixture set prefs `surfaceStyle: "solid"` (GlassPanel alpha fill đặc hơn) và ghi rõ trong PR body. Nếu grim latency > 80ms: mở rộng tolerance ±8 → ±(latency·0.09px/ms) và hẹp lại window mid [130, 210].

---

## 3. Ngân sách cap + gates

| Hạng mục | Kỳ vọng |
|---|---|
| MotionValue.qml | ~38 nonblank / 250 |
| ActivityIsland.qml | ~66 nonblank / 250 |
| test_island_motion.py | ~170-210 / 250 |
| test_island_motion_render.py | ~150-190 / 250 |
| Theme.qml | **253 pin — KHÔNG đổi** |
| Motion.qml | 25 — KHÔNG đổi |
| `check_architecture.py` | PASSED |
| `qmllint` MotionValue.qml + ActivityIsland.qml | sạch |
| G0 | **1453 + 9 = 1462 ran** (6 engine + 2 static + 1 render); kỳ vọng 1267+ passed / 190 skipped / ≤1 fail environmental |
| Deploy | không chạy trong PR (sau merge Agent-1 deploy + restart) |

G0 đỏ environmental danh sách đã chốt (backend_reconnect, test_catalog_failures settings-version, gowall_tree TimeoutExpired, first_frame_uses_saved_glass, managed_supervision quickshell_quit). Đỏ khác ⇒ rerun ×2 + A/B main cùng ngày.

---

## 4. Tasks (TDD — probe trước, test trước, QML sau, gates cuối)

### Task 0 — Probe (đã xong, ghi lại bằng chứng)
0a NumberAnimation-in-QtObject: PASSED (samples ở §0.2). 0b pixel-probe render: làm ở Task 4a TRƯỚC khi chốt render test.

### Task 1 — Branch + baseline
```bash
cd ~/lme-fedora-niri-qs && git checkout main && git pull --ff-only   # expect 165a72f
git checkout -b feat/island-morph
python3 scripts/check_architecture.py   # passed
grep -cv '^\s*$' qml/theme/Theme.qml    # 253
grep -cv '^\s*$' qml/theme/Motion.qml   # 25
grep -cv '^\s*$' qml/components/MotionValue.qml   # 16
grep -cv '^\s*$' qml/panels/ActivityIsland.qml    # 65
```

### Task 2 — Override test + RED trên main
1. Viết `~/glm-work/tests-overrides/a4b/{test_island_motion.py, test_island_motion_render.py, README.md}` theo §2 (render case để skip-guard sway/grim; chạy riêng sau).
2. Worktree main: `git worktree add --detach ~/glm-work/a4b-main 165a72f`; copy tests-local + 2 module mới vào `tests/`; chạy:
```bash
cd ~/glm-work/a4b-main && source ~/glm-work/venv/bin/activate
PYTHONPATH=scripts:tests python3 -m unittest test_island_motion -v 2>&1 | tail -12
```
**Expect RED: Ran 6, 6 fail/error** — engine ×5 với "Unable to assign to non-existent property morphMs" trong log; static fail. Lưu output. (Render module chạy ở worktree branch sau khi có GREEN — RED render = island spring → mid window fail; ghi chú nếu chạy.)

### Task 3 — Implement (GREEN) + mutations
1. Sửa 2 file đúng §1 (local clone → commit → push branch).
2. Worktree branch: `git fetch && git worktree add --detach ~/glm-work/a4b feat/island-morph`; copy tests như trên; chạy module → **Ran 6, OK**.
3. **M1:** sửa dispatch → `retarget(target)` → chạy → case 1/2/4/5 FAIL đúng lý do; revert → OK. **M2:** `duration: 420` literal → case 2/4 FAIL; revert → OK. Lưu cả 4 output.
4. Commit message: `feat(panels): the island's size morph rides the pill motion tokens`.

### Task 4 — Render seam
4a. Pixel-probe (script push qua oc.sh): grim latency ×5 + detectability island trên magenta (liquid vs solid). 4b. Chốt render test theo kết quả probe (window/tolerance/surfaceStyle), chạy tại worktree branch: **Ran 1, OK**; render tại main worktree 1 lần ghi nhận RED-geometry (mid window 460 ∉ [400,452]). 4c. `A4B_KEEP_PNGS=...` chạy lại lưu PNG mid/settled/close → `~/agent-collab/artifacts/a4b-island-{mid,settled,close}.png`.

### Task 5 — Caps + architecture + qmllint + G0
```bash
grep -cv '^\s*$' qml/components/MotionValue.qml qml/panels/ActivityIsland.qml
python3 scripts/check_architecture.py        # passed
qmllint qml/components/MotionValue.qml qml/panels/ActivityIsland.qml
git diff --stat origin/main                  # đúng 2 file
./scripts/run-gates.sh --gates G0            # expect 1462 ran
```

### Task 6 — Push + PR
`git push -u origin feat/island-morph` + PR qua API (body §5). Không đưa test vào PR.

---

## 5. PR body bắt buộc (đủ mục — thiếu = Agent-1 trả lại)

1. **Scope:** A4b wire ActivityIsland — PR đầu tiên của A4 đổi animation nhìn thấy; pill motion language (morph/shapeshift + morphCurve).
2. **Design:** opt-in `morphMs`/`morphCurve` trong MotionValue (7 consumer kia nguyên vẹn — static pin); dispatch onTargetChanged; snapTo shadow; enabled morph = Theme.animations. Bảng token wiring (width←morph 420, height←shapeshift 820, curve [0.16,1,0.3,1,1,1]).
3. **Behavior changes công khai** (§0.4): springMotion=false users; animations=false instant; raw overshoot biến mất.
4. **Files changed:** 2 file + nonblank counts; Theme 253 / Motion 25 untouched.
5. **TDD evidence:** RED main (6/6 + lý do); GREEN (6/6); M1 + M2 mutation outputs; render seam (mid window RED trên main qua geometry, GREEN trên branch, pixel ≈ logged ±8).
6. **Caps/gates:** nonblank ×2, architecture PASSED, qmllint sạch.
7. **G0 line nguyên văn** + xác nhận 1460 ran.
8. **Probe evidence:** 0a NumberAnimation samples; 0b grim latency + detectability (và surfaceStyle nếu dùng).
9. **Override:** `tests-overrides/a4b/` + md5 2 module.
10. **Not in this PR:** A4c polish, schema/prefs mới, pill nhỏ (rSmall/rTile), MotionAnimation/SlideLoader changes, mọi consumer khác.

---

## 6. Definition of Done + handoff

- Agent-2 journal: commit hash, diff --stat, RED/GREEN + M1/M2, nonblank, G0 line, override md5, PNG paths.
- **Agent-1 verify kép:** (1) diff đúng 2 file, khớp §1 nguyên văn; (2) tự chạy RED main + GREEN branch + M1/M2 + render; (3) caps/architecture/qmllint; (4) G0 máy mình 1462 ran (hoặc environmental đã biết); (5) đọc plan này đối chiếu từng số.
- Owner duyệt **PNG (mid/settled/close)** → merge → Agent-1 promote override a4b → tests-local + repo tests/, deploy (kỳ vọng 0 file changes) + restart shell.
- **Live acceptance (owner):** mở/đóng Activity Island: width morph lỏng ~0.42s, height nở ~0.82s đuôi dài, không nảy; ESC giữa mở → đảo chiều mượt; settings: animations off → tức thì; motionSpeed 2 → nhanh gấp đôi; springMotion off → flight đổi nhưng size morph vẫn pill language; switches/buttons/sliders (MotionValue khác) không đổi.
- Sau đó: A4c polish (Agent-2 tiếp).

## 7. Out of scope / cấm
- Không sửa Theme.qml (253), Motion.qml (25), SpringMotion.qml, SlideLoader.qml, MotionAnimation.qml, qmldir, THIRD_PARTY.md, schema/preferences/settings UI.
- Không wire consumer nào khác (A4c xét sau); không thêm token mới; không port reduceAnimations.
- Không promote tests-local trước merge; không deploy/restart trong PR; không đụng largeFiles/architecture.json.

## 8. Review Focus (edge đã tính)
- **NumberAnimation trong QtObject:** probe 0a PASSED; nếu một mai break (Qt upgrade) → fallback tự tính bezier trong FrameAnimation (§0.2) — không đổi contract.
- **Đảo chiều giữa chuyến bay** (mở + ESC nhanh): morphRetarget restart từ value hiện tại — test case 5 close-mid pin.
- **animations tắt giữa chuyến:** morphMs→0 (Motion.morph=0) ⇒ SpringMotion.onEffectiveReducedMotionChanged → snapTo (shadow stop animator) ⇒ snap sạch, không pixel kẹt giữa.
- **motionSpeed đổi giữa phiên:** binding duration re-evaluate; nhảy nhỏ chấp nhận được (token contract A4a case 2).
- **Warm-up/dormant:** snapTo vẫn tức thì (case 6 + island case cuối w==120/h==30).
- **7 consumer kia:** static pin không morphMs; enabled/retarget nhánh morphMs=0 đi đúng code cũ.
- **Clamp width/height giữ lại:** bảo vệ khi expandedWidth/Height thu nhỏ giữa chuyến (bezier từ trên xuống vẫn mượt).
- **Timer accuracy:** sampler 25-30ms, mọi window chừa biên ≥ 25ms hai phía; probe xác nhận Timer ổn định offscreen.
---

## 9. Hiện thực hóa khi implement (addendum 2026-11-15 — không đổi hợp đồng §0-§8)

1. **Backend settings push revert prefs:** probe timeline cho thấy snapshot prefs áp dụng tức thì nhưng bị backend push lại giá trị gốc đúng lúc `backendReady` flip (~+250ms). Engine cases 3/4/5 chờ `backendReady` TRƯỚC khi set prefs (house pattern của test_wifi). A4a test_motion_tokens từng pass nhờ đọc trước +150ms — timing luck, không phải hợp đồng.
2. **Render fixture dùng reopen:** lần mở đầu incubate content (first-paint ~200-300ms, expandedHeight wobble 656→679→621 do card load) — mid-flight đo trên lần mở 2 (tree retained, paint ngay, target ổn định).
3. **Grim latency 64-65ms đo được** → tolerance mid-flight ±10px; render test có retry ×2 (một lần sway/paint chậm không được phép flake gate).
4. **Close morph bị dormant snap cắt ở ~60-280ms** (exit flight đến outsideViewport nhanh — hành vi CŨ của SlideLoader, không phải regression): window close-morph [5, 350]ms thay vì [60, 350].
5. **qmllint:** MotionValue.qml rc 0 sạch; ActivityIsland.qml rc 255 **pre-existing trên main** (SpringMotion.qml cũng 255 — stock qmllint không resolve Quickshell types); diff của ta không thêm type mới.
6. **Đếm case:** engine module 8 test method (6 engine + 2 static) + render 1 = **9 case mới → G0 1462 ran** (§3 đã sửa).
7. **Probe 0a samples (bằng chứng §0.2):** NumberAnimation trong QtObject animate property chính nó: 30ms→41% (lý thuyết y=0.407), ~210ms→95%, settle ~420ms, không overshoot.
