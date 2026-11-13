# A2 deployment runbook — harness → máy user (agent qua OpenCode gateway)

> Dùng khi user gửi lại OC_URL/OC_AUTH (sandbox /tmp bị xoá giữa các session).
> Protocol: SKILL-remote-opencode (base64 byte-exact, STOP-gate, honesty clause).

## GLM-side runbook (raw shell qua `tools/rsh.sh`)

```bash
# 0. setup env (một lần)
export OC_URL=... OC_AUTH=...   # từ user; tạo ~/.oc-env (600)

# 1. tạo cây thư mục trên máy user
rsh.sh 'mkdir -p ~/dev-memtest/configs ~/dev-memtest/results/logs'

# 2. chuyển 17 file byte-exact (mỗi file: base64 → decode → wc -c đối chiếu)
#    (script helper bên dưới tự đọc MANIFEST + file local rồi bắn qua rsh.sh)

# 3. verify
rsh.sh 'cd ~/dev-memtest && sha256sum -c MANIFEST && chmod +x fakejava run_baseline.sh *.py'

# 4. tạo session agent + switch model + bắn prompt (phần dưới)
oc.sh new /home/kimhoanglong        # → SID
oc.sh set-model opencode/deepseek-v4.1-flash
oc_prompt.py <SID> deploy-prompt-a2.md
oc_report.py <SID> wait             # STOP-gate: chờ report
```

Helper transfer (chạy từ sandbox, thư mục `tools/memtest/`):

```bash
for f in $(awk '/^[0-9a-f]{64}  /{print $2}' MANIFEST); do
  b64=$(base64 -w0 "$f")
  rsh.sh "printf %s '$b64' | base64 -d > ~/dev-memtest/$f" || exit 1
  rsh.sh "wc -c ~/dev-memtest/$f"
done
```

## Agent prompt (gửi nguyên văn — dán vào session agent)

```
NHIỆM VỤ A2 — tái đo baseline Minewrap v1.9.3 bằng harness ~/dev-memtest/
(GLM đã chuyển sẵn + bạn đã verify sha256sum -c MANIFEST OK).

BỐI CẢNH: Minewrap = Rust workspace (github.com/longme179/Minewrap @ bfde421,
v1.9.3). Harness ~/dev-memtest/ là toolkit đo RAM ĐỘC LẬP (chính sách Q8:
KHÔNG bao giờ commit nó vào repo Minewrap; không đụng gì tới repo GitHub).

LÀM THEO ĐÚNG 6 BƯỚC, đánh số kết quả từng bước trong report. Không tự ý
mở rộng phạm vi. Không bịa số — cái gì chưa verify thì ghi "unverified".

1. ENV-CHECK (ghi vào ~/dev-memtest/results/env-check.md, phần "Máy user"):
   rustc --version; cargo --version; pnpm --version; node --version;
   tauri CLI (pnpm tauri --version hoặc cargo tauri --version);
   Xvfb có sẵn không (command -v Xvfb); echo $XDG_SESSION_TYPE;
   WAYLAND_DISPLAY + XDG_RUNTIME_DIR có set trong shell của bạn không.

2. LẤY SOURCE + BUILD (checkout RIÊNG, không đụng repo đang có của user):
   git clone https://github.com/longme179/Minewrap ~/dev-memtest/build/Minewrap
   cd ~/dev-memtest/build/Minewrap && git checkout bfde421
   cargo build --release -p minewrapd        # ~vài phút
   Ghi lại thời gian build + kích thước binary (ls -l target/release/minewrapd).
   BUILD GUI: theo README repo (pnpm install + pnpm tauri build — đọc
   package.json/scripts để dùng đúng lệnh). Nếu build GUI lỗi, ghi lỗi
   nguyên văn rồi vẫn chạy bước 5 phần daemon (GUI bỏ qua, ghi "skipped").

3. SMOKE S0 (chỉ nghiệm cơ chế, 10 giây):
   cd ~/dev-memtest && python3 scenario.py --config configs/idle0.toml \
     --binary ~/dev-memtest/build/Minewrap/target/release/minewrapd \
     --label S0-smoke --seconds 10
   Kỳ vọng: procs=1, threads=13 (máy 12 lõi), RSS ~5.5 MiB, min≈max.
   Nếu threads khác 13 hoặc số lệch xa >1 MiB → DỪNG, báo ngay.

4. CHẠY ĐẦY ĐỦ (RUNS mặc định 2; tổng ~10 phút):
   cd ~/dev-memtest && ./run_baseline.sh \
     ~/dev-memtest/build/Minewrap/target/release/minewrapd \
     <đường-dẫn-minewrap-tauri-nếu-build-được>
   Muốn cả SW2: SW2=1 ./run_baseline.sh ... (khuyến nghị chạy SW2=1).
   GUI display: nếu shell có WAYLAND_DISPLAY → chạy trực tiếp (đúng session
   user). Nếu không → chạy GUI dưới Xvfb: GUI_DISPLAY=xvfb DISPLAY_VAL=:99
   (khởi Xvfb :99 -screen 0 1280x800x24 & trước đó). Ghi rõ cách nào đã dùng.

5. KIỂM TRA KẾT QUẢ:
   cat ~/dev-memtest/results/baseline-v1.9.3.md
   Mỗi kịch bản phải có đủ samples (≥ seconds-2). Đối chiếu ngưỡng §15.4
   (đã in sẵn trong báo cáo). FAIL kịch bản nào → liệt kê + kèm Δ số.

6. STOP-GATE — REPORT RỒI DỪNG:
   In NGUYÊN VĂN nội dung results/baseline-v1.9.3.md + bảng env-check +
   danh sách file CSV đã tạo (ls results/) + ghi rõ những gì CHƯA verify.
   KHÔNG commit/push gì cả. KHÔNG sửa code Minewrap. Chờ GLM review —
   GLM sẽ tự tái đo ngẫu nhiên ≥1 kịch bản để kiểm chứng (rule: không tin
   số chưa verify). Nếu số sai, GLM sẽ yêu cầu chạy lại kèm điều chỉnh.

Lưu ý kỹ thuật đã biết (đừng "sửa" — đây là hành vi v1.9.3 có chủ đích ghi
nhận): REST GET /instances/{id} luôn trả combined_state "offline" kể cả khi
server đang chạy (GapB); token ở <data_dir>/token; các config dùng port
8081–8085 — đảm bảo không có gì chiếm các port này (ss -tlnp | grep 808).
```

## Sau khi agent report

1. GLM tái đo ngẫu nhiên ≥1 kịch bản qua rsh.sh (gọi thẳng scenario.py).
2. Đối chiếu §15.4; FAIL lớn → điều tra môi trường (kernel, build flags,
   font/GTK env cho GUI) TRƯỚC khi làm P0.
3. Fetch kết quả về sandbox (oc_fetch.py) → commit vào archive repo
   `tools/memtest/results/baseline-2026-11-11/`.
4. Báo user: bảng baseline + đề xuất mở Phase B (branch p0-daemon-first,
   B1–B9) + Phase C (C0 spec → 3 spike agent sessions).
