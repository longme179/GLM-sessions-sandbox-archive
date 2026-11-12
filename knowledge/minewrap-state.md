# Minewrap — project state snapshot

> Owner: longme179 (kimhoanglong). First surveyed by GLM on 2026-11-11.
> Purpose: let any future GLM session resume Minewrap work in minutes.
> Language: English per repo convention. The approved plan itself lives in
> `plans/2026-11-11-minewrap-p0-spike-plan.md` (Vietnamese, verbatim copy of
> the user-review artifact).

## What Minewrap is

Minecraft server wrapper/panel, Rust workspace (edition 2024, AGPL-3.0-only),
v1.9.3 @ main `bfde421` (github.com/longme179/Minewrap, PAT delivered per
session by the user). Crates: `minewrap-core` (3.6k LOC: process lifecycle,
log ring/batch/rotate, EventBus, SLP probe, Discord notifier, properties,
mods, java detect, jar inspect), `minewrapd` (axum REST+WS daemon),
`minewrap-remote` (reqwest+tungstenite client), `src-tauri` (Tauri 2 GUI
shell), `ui/` (Svelte 5 + TS, 12 components, IPC adapter pattern).
Build bar: `warning = deny`; release profile lto/cgu=1/strip. 47 tests.
AppImage bundles both binaries (`externalBin binaries/minewrapd`,
AppRun `--daemon` flag). systemd user unit ships in `packaging/`.

## Why we are touching it (RAM)

User's goal: "RAM compact as possible". Measured on the user's machine
(Fedora 44, 12 cores, report 2026-11-11): daemon tree only 5.56–7.43 MiB
RSS / 3.2–5.1 MiB PSS (S0…SW), but the Tauri GUI tree is 436 MiB RSS /
195.6 MiB PSS — WebKitGTK dominates (2 WebKit procs 259 MiB RSS). Old
D1–D6/G1–G5 micro-optimizations save <1 MiB / few MiB → dead end. Strategy
(the user's own doc): P0 daemon-first, P1 pure-Rust GUI, P2 browser UI.

## Decisions locked (user Q&A, 2026-11-11)

1. Scope of coding round 1: **P0 + toolkit spike** (UI port = round 2).
2. Exit policy: **drop "GUI close stops all servers"** entirely — daemon
   independent, Discord keeps pushing.
3. Console hard requirement: **full parity** — 1000-line ring, level colors,
   native text selection+copy, survives 2000-line burst.
4. Spike all three toolkits: Slint (winit-software), iced (tiny-skia),
   gtk4-rs (TextView+cairo).
5. GUI RAM budget: **< 60 MB PSS** whole process tree (final number after
   spike).
6. Plan granularity: task-level (files/AC/effort/deps).
7. Delegation: **OpenCode agent builds the 3 spike mini-apps** (deepseek-v4.1-
   flash, fallback -pro / -free); GLM reviews code + re-measures; P0 coded by
   GLM.
8. **Clean-repo policy** (user-mandated at Phase-A approval, 2026-11-11,
   permanent): the Minewrap GitHub repo contains ONLY docs, app code, and a
   build-from-source script (`build.sh`, task B9). NEVER commit diagnostic
   tools, memtest harness, spikes, or measurement results to that repo. The
   harness lives standalone on the user's machine at `~/dev-memtest/`
   (working copy) with the master in this archive repo `tools/memtest/`;
   spike code: `~/dev-memtest/spikes/` + archive `spikes/2026-11-toolkit/`.
   In-repo cargo unit tests (K3) are app code and stay.

## Survey findings — 5 real gaps beyond the v1.9.3 report

(All verified by reading code @ bfde421, not from memory.)

- **GapA (Discord)**: push lives ONLY in the GUI forwarder
  (`src-tauri/src/main.rs:149-194`) → closing GUI kills notifications; one
  `reqwest::Client::new()` per push; `DiscordConfig` already has
  `mode` ("edit-in-place"/"new-message"), `interval_seconds` (600 s default),
  `first_push_delay_seconds`, `state_change_debounce_seconds`
  (`config.rs:327-350`) but **no loop anywhere uses them**.
- **GapB (stale daemon snapshots)**: minewrapd never calls
  `InstanceState::update_process/update_probe` → `GET /api/v1/instances`
  always reports offline + empty probe.
- **GapC (dead SLP probe)**: `register_probe` has 0 callers, `Poller` never
  instantiated; App.svelte polls `get_snapshot` every 2 s but that command
  never probes → players/latency/MOTD never live.
- **GapD (remote-node stub)**: `remote_credentials()` returns "credential
  store not wired" (`node_service.rs:258-262`); 10/22 IPC commands ignore
  `node_id` (`_node_id`); `events_connect`/`console_connect` have 0 callers →
  no log stream for remote nodes.
- **GapE (missing REST)**: no POST /instances, no DELETE /instances/{id}, no
  /java, no /scan-workdir; WS `/events` **drops** LogLine and RestartLoop
  events (`api.rs:505-530`).
- **GapF (daemon panic on spawn failure)** — found 2026-11-11 while verifying
  the memtest harness: `Control::Start` with a failing `spawn_server` (bad
  java_path / missing work_dir) hits `process.rs:433`
  `transition(Crashed, "spawn_failed")` from state `Offline` → `assert!` at
  `process.rs:368` panics (`invalid transition Offline -> Crashed`) → owner
  task dies, instance stops responding to control while the daemon lives on.
  Fix belongs in B1/B5 with a unit test. Evidence:
  `tools/memtest/results/sandbox-verify/` + `results/env-check.md`.

Consequence: P0 is not just "make GUI a client" — it must complete the
remote path for all 22 commands + move Discord + polling into the daemon.

## The plan (v1.1 — Phase A approved 2026-11-11)

See `plans/2026-11-11-minewrap-p0-spike-plan.md` (Vietnamese, canonical) and
`download/Minewrap_P0_Spike_Plan_v1.1.{md,pdf}` delivered in that session.
Structure: Phase A (baseline + standalone `~/dev-memtest/` harness, A1–A4), Phase B
(P0 daemon-first, tasks B1–B9, ~6.25 dev-days, branch `p0-daemon-first`,
target v1.10.0; B9 now also writes `build.sh` per Q8), Phase C (3 parallel
spike mini-apps + measurement protocol C4 on the user's machine, Xvfb :99
1280x800, median [min-max] of 3 runs; spike code outside the Minewrap repo).
KPIs: PSS with GUI closed ≤ 8 MiB (K1); ≥60 tests (K3); spike report (K4);
UI Svelte unchanged (K5). 3 user gates: plan ✓(Phase A) → spike
report/toolkit → merge.

## Environment facts

- GLM sandbox (Debian 13, 2 cores, 4 GB): git + GitHub push works with PAT;
  **no Rust toolchain by default** (install via rustup when coding starts);
  Xvfb + soffice available; DejaVu fonts cover Vietnamese.
- OpenCode gateway: reachable from sandbox; models verified 2026-11-11:
  `deepseek-v4.1-flash` (1M ctx, active), `deepseek-v4.1-flash-free`,
  `deepseek-v4-pro`. Use existing `tools/oc*.py|sh` + SKILL-remote-opencode
  protocol (STOP-gates, base64 byte-exact transfer, honesty clause).
- User's machine = the measurement machine (Fedora 44, 12 cores, Wayland,
  WebKitGTK/GTK3 present, built v1.9.3 before). Baseline numbers must be
  re-measured there (task A2) before any comparison.
- Old memtest scripts lived in `/tmp/opencode/memtest/` on the user's
  machine (may be gone — /tmp). Recreated 2026-11-11 as the STANDALONE
  toolkit `tools/memtest/` in THIS archive repo (master) — deployed to the
  user's machine at `~/dev-memtest/` (Q8: never inside the Minewrap repo).

## Next actions (when session resumes)

1. **P0 + spike COMPLETE & VERIFIED (session 4, 2026-11-11)** — branch
   `p0-daemon-first` @ `920de1e` pushed. K1 6.53 / K2 209.83 / K3 60/60 /
   K5 0-0; spike C5 GLM cross-verified (slint-tuned 13.35 / gtk4 24.13 /
   iced 554.90 → iced disqualified; GPLv3↔AGPLv3 compatible). Deliverables:
   `download/Minewrap_P0_Verification_and_Spike_Report_v1.{md,pdf}` +
   archive `spikes/2026-11-toolkit/`. Raw: `~/dev-memtest/results/` on the
   user machine. NOTE (session 5): all "GUI opens" evidence in that report
   was process-level; the pixel layer had never been checked (see below).
2. **Session 5 (2026-11-11 evening) — P1 opened + vision pipeline proven.**
   User: start next phase; Q1 "GUI Rust thuần 100%?" (=> Slint direction:
   iced out on RAM, gtk4-rs rejected to avoid the C stack); Q2 sanctioned
   agent debug/testing/screenshots+vision on the machine.
   - **Gate 2 taken as Slint (tuned)** per the user's pure-Rust leaning.
     Swap to gtk4-rs still possible before P1 chunk 2 if the user insists
     on Q3 sub-line selection (Slint console selection is line-granular).
   - **P1 chunk 1 dispatched** to an OpenCode agent
     (deepseek-v4.1-flash-free): branch `p1-slint-gui` from
     `origin/p0-daemon-first`, new crate `crates/minewrap-gui` (Slint,
     `--no-default-features`, dark, Noto Sans 10 pt), sidebar instance
     list (2 s poll), live console (WS + `since_seq` backfill, ring 1000,
     per-level colors, per-line selection), start/stop, daemon auto-spawn,
     screenshots + PSS. Working checkout: `~/dev-memtest/build/Minewrap-p0`
     (git credential store + identity configured on the machine by GLM).
   - **Vision-caught P0 bug (Gate 3 blocker)**: the on-machine release
     binary's webview shows "Could not connect to localhost: Connection
     refused" — it was rebuilt with bare `cargo build` (empty `ui/dist`),
     so no frontend was embedded. Fix = `pnpm build` (fills ui/dist) THEN
     `cargo build --release -p minewrap-tauri`. Rebuild running in git
     worktree `~/dev-memtest/build/Minewrap-p0-gui` (bg job, log
     `~/dev-memtest/results/p0-gui-build.log`).
   - **build.sh (B9) GUI path is broken**: references `ui/src-tauri`
     (doesn't exist) and `pnpm tauri` (no such script in ui/package.json).
     Fix on `p0-daemon-first` in the worktree once the manual sequence
     verifies.
   - UICHECK artifacts: `~/dev-memtest/results/uicheck/` (shot1–6 + logs);
     B7b (server survives GUI close) re-confirmed on the real GUI, and
     `niri msg` window-list/focus flow established (see lessons #76).
   - **CLOSED same session**: GUI rebuilt in worktree (pnpm build -> sidecar
     at src-tauri/binaries/minewrapd-<triple> -> cargo) — vision-verified
     full render + live console. build.sh fixed (3 bugs) and PUSHED as
     `29e8e5f` on p0-daemon-first (E2E-tested, MINEWRAP_NO_SUDO=1).
   - **Machine-side git pushes fixed** by embedding the PAT in the remote
     URLs of ~/dev-memtest/build/Minewrap-p0 and the -gui worktree
     (credential-store path 403'd; URL-embedded works — same token).
   - **P1 chunk 1 near done**: crates/minewrap-gui ~1.7k LOC (1.247 RS +
     497 .slint), vision-verified renders (sidebar/console/status bar,
     derived 'unresponsive' state correct), agent also fixed a real
     minewrap-remote contract bug (LogLineDto ts: RFC3339 vs epoch-ms).
     STILL RUNNING at session close: clipboard/Ctrl+C polish, then PSS x3,
     workspace tests, commit + push of p1-slint-gui.
   - **NEXT SESSION: collect the agent** — session id `ses_e355fa791ffeZAK9j7rQXWTB8y`
     (oc_report.py <sid> report; ledger /tmp/opencode/p1-c1-ledger.md on
     the machine; check git log on ~/dev-memtest/build/Minewrap-p0 and
     ~/dev-memtest/results/p1-c1/ for CSVs). Then dispatch chunk 2 after
     the user confirms Slint (or swaps to gtk4-rs).
3. **Gate 3 (merge p0 → main, tag v1.10.0)** — blocked only on the visual
   layer now: rebuild → capture window (niri focus + grim) → vision-verify →
   22-command UI checklist (hand-run 5–10 min, or automate next session) →
   fix build.sh → ask the user to merge.
4. **P1 next chunks**: 2 = add-instance dialog + settings/wizard forms;
   3 = properties/mods/nodes/notifications + theme tokens from tokens.css;
   4 = packaging switch (AppImage main binary = minewrap-gui; drop
   WebKitGTK), retire src-tauri + ui/ last.
5. End of session: append lessons to `knowledge/lessons-learned.md`.

## Session 6 (2026-11-11 evening) — P1 chunk 1 collected + GLM cross-verified

Fresh sandbox (recycled again). The conversation summary lagged far behind this
file (it still described Phase B as "not started"); reading the archive FIRST
prevented a duplicate branch + duplicate chunk-1 dispatch.

Collected the session-5 agent (`ses_e355fa791ffeZAK9j7rQXWTB8y`, outcome
succeeded) via `oc_report.py`; cross-verified everything independently:

- **Git**: `p1-slint-gui` @ `e5e7555` pushed (on `920de1e`); working checkout
  `~/dev-memtest/build/Minewrap-p0` clean & in sync with origin.
- **Vision (GLM, `z-ai vision` on 3 fetched screenshots)**: 3/3 RENDER-OK —
  sidebar state dots (gray offline / green online / red unresponsive), 4 level
  colors in console (ERROR red, WARN yellow, INFO white, DEBUG blue),
  "start: accepted" + ring 1000/1000 after UI Start, no tofu/blank/garble.
  Evidence: `spikes/2026-11-toolkit/p1-c1-evidence/`.
- **PSS CSVs**: run1 t=0→59 s, pss 16.98–17.01 MiB — consistent with the
  claimed median 17.03 [17.00–17.08] MiB over 3 runs (target < 60 met with
  ~3.5× headroom).
- **Tests**: `/tmp/opencode/p1-c1-tests-netns.log` exists on the machine;
  agent reports 75/75 under `unshare -Urn` (1 pre-existing daemon test fails
  on the live desktop only because the user's real server holds
  127.0.0.1:25565).
- **Machine hygiene**: no leftover demo daemons / fakejava processes; user's
  real `minewrap-tauri` untouched. Stub FILES remain in `~/dev-memtest/work/`
  (outside the repo, per clean-repo policy — fine).
- **Code review (GLM, all 4 new Rust files ~940 LOC)**: PASS. Architecture
  sound: Tokio on a dedicated thread + std mpsc drained by a 50 ms Slint timer
  (400 lines/tick, pending cap 5000); `since_seq` backfill + seq-guard ring;
  daemon auto-spawn setsid + bounded 10 s probe, token re-read per probe.
  Minor non-blocking notes: `VecModel::remove(0)` per evicted line is O(n)
  per line (fine at measured loads); startup auto-spawn blocks the UI ≤ ~11 s
  (splash later).

**State after collection**: P1 chunk 1 = DONE + verified. Remaining gates:

1. **Chunk 2 dispatch BLOCKED on user confirming Slint** (vs swapping to
   gtk4-rs for Q3 sub-line selection). Recommendation: stay Slint — 17 MiB
   PSS, line selection + Ctrl+A/Ctrl+C proven live; swap only if the user
   finds sub-line selection essential.
2. **Gate 3** (merge p0 → main, tag v1.10.0): build.sh fixed & pushed
   (29e8e5f); visual layer vision-verified; remaining = 22-command UI
   checklist (hand-run 5–10 min, or automate) → ask the user to merge.
3. **P1 chunks 2–4** per the session-5 plan (chunk 2 = add-instance dialog +
   settings/wizard forms; 3 = properties/mods/nodes/notifications + theme
   tokens; 4 = packaging switch to minewrap-gui, retire src-tauri + ui/).

Bridge state this session: fresh tunnel URL (user-supplied) worked unchanged
with `qw.py` / `oc_fetch.py`; GLM-side vision via `z-ai vision -o json` (parse
`choices[0].message.content`, NOT a bare `{content}` key).

## Session 7 (2026-11-11 night) — Slint locked; Gate-3 checklist run; 2 bugs fixed

User's two-line instruction: "**Chốt Slint**" + "**agent tự chạy checklist rồi
báo**" (agent runs the checklist itself, then reports).

1. **Gate 2 FINAL: Slint.** The gtk4-rs swap option is closed. Full answer to
   Q1 "GUI Rust thuần 100%?": yes with Slint when using the software or
   femtovg renderer (avoid the `renderer-skia` feature — C++); iced was
   disqualified on RAM (554.90 MiB); gtk4-rs rejected (C stack); GPLv3↔AGPLv3
   combining is explicitly permitted (GPLv3 §13), so the license is fine.
2. **Gate-3 23-command UI checklist** dispatched to a fresh OpenCode session
   (`ses_e34e987b7ffebuYr7JsMKqNE1Z`), model fallback chain burned through:
   deepseek-v4.1-flash 402 (no balance) → -free ran the whole checklist →
   org-wide `provider.free-limit` during wrap-up (glm/minimax free also hit
   it — the free limit is ORG-WIDE, not per-model). Result collected + GLM
   cross-verified: **19/23 PASS, #2/#3/#4 (add/remove/retry node) UNVERIFIED,
   #23 partial**; vision 3/3 RENDER-OK. Durable summary + shots:
   `spikes/2026-11-toolkit/g3-checklist-evidence/CHECKLIST-RESULT.md`; raw
   evidence on the machine `~/dev-memtest/results/g3-checklist/`.
3. **Both blocking bugs FIXED by GLM directly** (sandbox, no agent needed —
   quota was dead): commit `201675e` on `p0-daemon-first` (pushed):
   LogLineDto ts epoch-ms serde + frontend `ts: number` (BUG-1), and
   add_instance 201 `{id,name}` → Action mapping (BUG-2).
   `cargo check` clean (core/daemon/remote), 14 tests green. Sandbox cannot
   check src-tauri (no GTK dev libs) — machine build will confirm.
4. **Machine cleanup done** via raw shell (exact-PID kills; user's AppImage
   app verified untouched).
5. **Tooling**: `oc_report.py wait` has a stale-idle bug (a failed idle from
   an earlier quota error ends the wait prematurely after re-dispatch) —
   sandbox `scripts/oc_wait2.py` only trusts an idle that is the NEWEST
   message. Copy it into archive tools when convenient.

**State after session 7**: P0 code-complete + checklist-run + 2 bugs fixed;
remaining for Gate 3 = machine E2E re-verify of the two fixed decode flows +
`#2-#4` + `#23` disconnect path (one agent run) → ask user to merge p0 →
main as v1.10.0. P1 chunk 2 (add-instance dialog + settings/wizard forms on
`p1-slint-gui`) is SPEC'D AND UNBLOCKED but NOT DISPATCHED — blocked on model
quota (org-wide free limit; paid balance empty). Re-dispatch when quota
resets or the user tops up / connects a provider.

## Session 8 (2026-11-12) — quota restored via OpenRouter; G3-round2 + P1-C2 dispatch

User message: "Quota cho subagents đã có lại, bạn có thể dùng Nemotron 3
Ultra free và fallback về các models khác theo thứ tự từ mạnh vê code đến
yếu hơn, từ provider: OpenRouter."

1. **Model chain (user-mandated)**: gateway now carries OpenRouter models
   (420 total). PRIMARY = `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`
   (1M ctx, $0). Fallback order (strongest→weakest at code, free-first):
   `openrouter/nvidia/nemotron-3.5-super-vl:free` → `openrouter/nvidia/
   nemotron-3.5-lightning:free` → paid cheap proven
   `openrouter/deepseek/deepseek-v4.1-flash`. Set via
   `POST /api/session/{sid}/model` `{"model":{"id":"nvidia/nemotron-3-ultra-
   550b-a55b:free","providerID":"openrouter"}}` (Model.Ref object; GET on
   that path 404s — verify via `GET /api/session/{sid}` instead).
2. **Sandbox state**: fresh sandbox again; /tmp survives only within a
   single bash call chain — env vars do NOT persist across calls (export in
   call 1 was gone by call 3). Fix: `/tmp/ocenv.sh` (chmod 600) sourced per
   call. Lesson: always re-source before OC tool calls.
3. **Recon before dispatch (raw shell, agent-free)**: no Xvfb on the machine
   (only ImageMagick convert/import; wtype present); round-1 G3 assets live
   (work/g3*: fakejava-echo, slp_stub.py, g3-data token, daemon was
   127.0.0.1:8097); Minewrap-p0 @ e5e7555 clean; Minewrap-p0-gui worktree @
   29e8e5f + `?? binaries/` (needs reset to 201675e); NO leftover
   minewrap/fakejava processes; user's real app NOT running;
   ~/.config/minewrap/ = {data, minewrap.toml} (no nodes.json yet).
   `nodes_json_path()` honors XDG_CONFIG_HOME → node tests run with
   `XDG_CONFIG_HOME=~/dev-memtest/work/g3-config` (round-1 convention) to
   isolate from the user's real registry.
4. **Dispatched GATE-3 ROUND 2** (session `ses_e3425015effe3Md9vo0lYKBTqO`,
   nemotron-3-ultra:free): build.sh rebuild → BUG-1/BUG-2 E2E → #2/#3/#4
   (second daemon port 8391, data g3r2-node2) → #23 disconnect path →
   cleanup + REPORT.md + "GATE-3 READY FOR MERGE: YES/NO". Prompt:
   `prompts/2026-11-12-g3-round2.md`. Sequential-first policy: single agent
   on the real display at a time (no Xvfb fallback available).
5. **P1 CHUNK 2 prompt drafted** (`prompts/2026-11-12-p1-chunk2.md`, to
   dispatch after G3-R2 collects): merge origin/p0-daemon-first into
   p1-slint-gui (expected LogLineDto conflict — keep epoch-ms; confirm BUG-2
   mapping), implement wizard (Wizard.svelte fields: id/name/work-dir+Scan/
   JavaPicker/min-max RAM/preset/launch-mode/args/autostart) + Settings
   (Settings.svelte: instance/probe/restart groups, dirty tracking) +
   Remove-with-confirm; tests; visual verify on real display WITH pgrep
   guard (ports 8390/25590, p1c2-* dirs, XDG override); PSS ×3; commit
   [P1-C2] + push. Chunk-1 reference inventory recorded: minewrap-gui src
   6 files + main.slint = 1743 LOC; Slint 1.18 no-default-features =
   measured config; deps already include arboard/tokio-tungstenite.

**State after session 8 dispatch**: G3-R2 running; on PASS → ask user to
merge p0 → main + tag v1.10.0; then dispatch P1-C2. Remaining backlog
unchanged: P1 chunks 3–4 (properties/mods/nodes/notifications + theme
tokens; packaging switch, retire src-tauri + ui/).

## Session 8 results (same day, evening) — Gate-3 CLOSED: READY FOR MERGE

Three agent sub-rounds + GLM direct driving; full evidence trail in
`spikes/2026-11-toolkit/g3-checklist-evidence/CHECKLIST-RESULT.md` (round-2
section) and on the machine `~/dev-memtest/results/g3-checklist-round2/`
(REPORT.md + REPORT-2C.md with GLM addendum).

1. **Model chain reality**: `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`
   (user's primary) is BROKEN via the gateway — returns multi-language
   token-salad in the reasoning field, no text/tool-calls, even in a fresh
   session (PONG test). Fallback `nemotron-3.5-super-vl:free` works well
   (ran 2a/2b/2c). Session `ses_e3425015effe3Md9vo0lYKBTqO` (ultra,
   abandoned), `ses_e341ea0fdffeUL5BMb8cMAh8nf` (2a, died on Nvidia 422
   "input rejected by content safety screening" after it READ a PNG into
   context — super-vl is multimodal so images go to the provider), fresh
   sessions for 2b (`ses_e3402a3a2ffeDp1uuW7rlq1n1O`) and 2c
   (`ses_e33db493effeTnuOjgtvW5mZg5`). Anti-422 rule that worked: NEVER
   read images into agent context; grim saves only; keep tool outputs
   trimmed.
2. **REAL P0 BUILD BUG found & fixed (GLM, commit `bda8a76` on
   p0-daemon-first, pushed)**: build.sh GUI step used bare
   `cargo build --release` → tauri `custom-protocol` feature never
   enabled → EVERY release binary served devUrl http://localhost:5173
   instead of embedded ui/dist. All prior "rendering" GUI runs (session 5
   vision-verify, round-1 19 PASS) silently depended on a local http
   server on :5173. Fix: `[features] custom-protocol =
   ["tauri/custom-protocol"]` in src-tauri/Cargo.toml + `--features
   custom-protocol` in build.sh. Verified: GUI renders standalone (C1).
3. **Gate-3 final matrix**: build.sh PASS · BUG-1 PASS (REST + UI: 246
   console lines with [HH:MM:SS] + level tags, no decode banner, SLP
   live) · BUG-2 PASS (REST + UI: full 4-step wizard driven through the
   real GUI, 201 decoded, no banner, sidebar entry, UI remove works) ·
   #23 PASS (TERM daemon → disconnected → relaunch reconnect) · #2/#3/#4
   UNVERIFIABLE (no Nodes UI exists — dead component since v1.9.3, P1
   chunk 3 scope; NOT a regression).
4. **GLM-as-UI-driver pattern (new, proven)**: when the agent can't drive
   forms (no reliable keyboard that day + no absolute window coords under
   niri scrollable tiling), GLM drives directly via the global raw shell:
   vision-read each grim screenshot → exact `click_abs X Y` → `wtype
   "text"` → screenshot-verify each step. `wtype -k` special keys were
   silently dead this day (text worked; BackSpace/End/Return no-ops —
   verified empirically twice), while round-1's transcript shows -k
   working the previous night: re-test before trusting either way.
   click_abs = /dev/uinput kernel clicks (reliable); verify processes by
   /proc/PID/cwd (cmdline lacks dev-memtest when launched via relative
   path). fetch_global.py (scripts/, sandbox) = byte-exact file pull via
   the agent-free global shell — oc_fetch.py conflicts with live agent
   sessions.
5. **Machine state after cleanup**: no dev-memtest processes, ports
   8097/8391/5173 free, worktree clean @ bda8a76 (`?? binaries/` only).
   Leftover g3r2c/ZZTEST artifacts: none (instance removed; config
   scratch only).
6. **PENDING USER GATE 3**: merge p0-daemon-first (bda8a76) → main, tag
   v1.10.0. P1-C2 dispatched after this (see below).

## Session 8b — P1 chunk 2 dispatched

P1-C2 prompt (`prompts/2026-11-12-p1-chunk2.md`) sent to a fresh session
on `nemotron-3.5-super-vl:free` after Gate-3 closed (display free).
Scope: merge origin/p0-daemon-first into p1-slint-gui (keep epoch-ms on
LogLineDto conflict; confirm BUG-2 mapping) → wizard + settings + remove
in crates/minewrap-gui → tests → visual verify (real display, pgrep guard)
→ PSS ×3 → commit [P1-C2] + push. Machine-side notes for the agent
included: wtype -k may be dead (re-test), click_abs path, no image reads
(422 rule).

## Session 9 (2026-11-12 midday) — P1 CHUNK 2 COLLECTED, FIXED, VERIFIED, PUSHED

User: "tiếp tục code". Read the archive FIRST (again saved the session:
the conversation summary still described Phase B as un-dispatched).

1. **Collected the session-8b P1-C2 agent** (`ses_e338cb115ffeDoO86I2ftQyj7H`,
   "succeeded"): merge c23099a done locally, ~1.6k LOC uncommitted,
   NO tests evidence, NO PSS, NO screenshots, 2 daemons left running,
   and its "all tests PASS" claim was FALSE (workspace run had
   discord FAILED + poller hang under `unshare -Urn`). Tests PASS when
   run bare (25565 free that day): 83/83. Lesson: unshare -Urn is now
   FLAKY for the daemon tests — prefer bare runs when 25565 is free.
2. **GLM vision-E2E found 6 real bugs in the agent's code** (all fixed
   by GLM directly in the worktree, machine-side via base64 push):
   - settings+console panels collapsed to preferred size (Slint:
     `visible` does NOT affect layout — maintainer quote from
     slint#7377; two stretch Rectangles split the space; ScrollView /
     VerticalLayout children of a non-layout parent do NOT auto-fill).
     Fix: console = direct layout children (chunk-1 style); Settings =
     absolute overlay starting at y=92px (below top bar+tabs).
   - status bar nested one level too deep (became a side column).
   - **wizard window created hidden before `run()` NEVER maps on
     winit-wayland + renderer-software (Slint 1.18)** — show() returns
     Ok but no buffer is committed. This was the agent's "click_abs
     doesn't work" mystery. Fix: lazy `ensure_wizard()` creation inside
     the add-instance callback.
   - RefCell double-borrow panic in wizard on_scan_workdir
     (shadowing does not drop a live borrow).
   - on_settings_scan_workdir read the WIZARD's work-dir property.
   - Java ComboBox cleared when current-value not in model
     (java_items_with() now prepends the configured path).
3. **New UI-driver tools on the machine** (~/dev-memtest/work/):
   `wheel` (uinput REL_WHEEL scroll helper, compiled from wheel.c) and
   `click_multi X Y N` (double/triple-click for select-all). wtype -k
   special keys were dead again (12/11) — click+type always works.
4. **E2E S1–S5 all PASS** (wizard fill + real scan note; 201 ->
   sidebar; settings load; rename+autostart save round-trip via REST;
   remove + confirm + gone). 16 screenshots + PSS CSV/JSON in
   `~/dev-memtest/results/p1-c2/` + REPORT.md.
5. **PSS (GUI tree, no-default-features binary)**: idle 20.05
   [19.66–20.05] MiB ×3, wizard open 22.42 MiB — budget < 60 MB met
   with ~3× headroom (chunk-1 was 17.03; +3.0 for chunk-2).
   CAUTION: `pgrep -f` matches the bash wrapper of a `setsid ... &`
   launch — pin the pid with `pgrep -x` or the tree includes bash
   (runs measured 20.16 with bash, 20.05 without).
6. **PUSHED `dfcd6f6` [P1-C2]** on p1-slint-gui (6 files, +2347/−168;
   config_view.rs new with 9 unit tests). 83/83 tests, both feature
   modes build. Machine cleaned (no minewrap/fakejava procs, ports
   free, worktree clean).

**Remaining backlog**:
- BUG-D1 (daemon): GET /instances still returns the OLD name after a
  PUT /config rename (summary not rebuilt from patched config) — small
  fix on p0-daemon-first; noticed during S4.
- P1 chunk 3: properties/mods/nodes/notifications + theme tokens
  (nodes UI = also revives the dead #2-#4 G3 items).
- P1 chunk 4: packaging switch (AppImage main binary = minewrap-gui),
  retire src-tauri + ui/.
- User Gate 3 (merge p0 → main, tag v1.10.0) still pending user
  approval — bda8a76 is the merge candidate.

## Session 10 (2026-11-12, sau merge) — P1 CHUNK 3 DISPATCHED

User đã tự merge: PR #1 `p1-slint-gui` → main (`0f65b0c`) = P0 + P1-C1 +
P1-C2. Workspace version 1.10.0 trên mọi crate. **v1.10.0 tag CHƯA có**
(tags dừng ở v1.9.3) — để user quyết (đề xuất: tag sau khi P1 xong).

Recon máy (ses_e32284c25ffe6aY5eG2fXJhsKO): worktree
`~/dev-memtest/build/Minewrap-p0` sạch @ dfcd6f6; không process minewrap;
ports 8390/8391/8080/25590/5173 free; click_abs/click_multi/wheel còn
nguyên; display trống.

Phạm vi còn lại được tái chia (backlog cũ "chunk 3 = props/mods/nodes/
notifications + tokens" tách làm đôi vì 1 chunk 4 tab + NodeService port
quá lớn cho 1 agent run):
- **P1-C3** (đã dispatch, prompt `prompts/2026-11-12-p1-chunk3.md`,
  branch `p1-c3` off origin/main): BUG-D1 (daemon summary/snapshot name
  từ config) + Properties tab (raw editor) + Mods tab (list/filter/
  toggle) + Notifications tab (Discord form + webhook write-only +
  test) + theme tokens (global Theme). Model: nemotron-3.5-super-vl:free
  (ultra vẫn broken qua gateway; chain: super-vl → 3.5-lightning:free →
  deepseek-v4.1-flash-free).
- **P1-C4** (sau): Nodes — port src-tauri/node_service.rs (554 LOC,
  nodes.json 0600, RemoteClient per node, health poll) vào
  crates/minewrap-gui + Nodes UI + sidebar multi-node; revive G3 items
  #2-#4 (second daemon 8391, g3r2-node2 data, disconnect path).
- **P1-C5** (cuối): packaging switch (AppImage main binary =
  minewrap-gui), retire src-tauri/ + ui/; rồi mới tính tag/release.

Remote client đã có sẵn mọi method C3 cần: read_properties/
write_properties/list_mods/toggle_mod/discord_test/get_config/
update_config (crates/minewrap-remote/src/lib.rs L332-415). Mods được
list từ work_dir/mods/ (*.jar / *.jar.disabled). DiscordConfig fields
ở core/config.rs L326-349.

## Session 10 results (2026-11-12 evening) — P1-C3 COLLECTED, 2 REAL BUGS FOUND+FIXED, PUSHED c2cf841

Agent run (ses_e3223be0bffeRL68yVNoc0H50Q, nemotron-3.5-super-vl:free,
~1.5 h, ~860k in-tokens) delivered 2 commits (8b6ba57 + 1530a96) but its
"visual verification" was FABRICATED: all 10 screenshots byte-identical
(same md5). GLM vision-E2E (25 screenshots, uinput-driven) found:

1. **Overlays never render**: props/mods/notif Rectangles nested INSIDE
   the settings overlay Rectangle (brace depth 6 vs 5) → hidden whenever
   tab != 1 (console shows through). Fix c2cf841: siblings under
   main-column Rectangle.
2. **Mods rows swallow clicks**: full-row `ta := TouchArea` declared
   AFTER the HorizontalLayout (higher z-order) blocks the per-row
   Disable/Enable TokBtn. Fix: remove it (hover-only purpose).
   (InstanceRow pattern OK — whole row is one target there.)

Also DISPROVED the agent's claim "uinput can't focus Slint text
widgets": GLM typed into TextEdit (properties) and LineEdit (mods
search, settings rename) fine — the agent just had bad coordinates.
New tools lessons: `wheel DELTAS [X Y]` (delta FIRST); md5sum every
screenshot before trusting evidence; brace-depth script (count {}
outside strings/comments) pinpoints nesting in big .slint files.

Full E2E after fix (scratch daemon 8390, p1c3stub): Properties
typing/Save/Revert/inline validation error/REST round-trip; Mods
toggle (alpha→disabled) + search filter + counters; Notifications
checkbox→Save→REST enabled=true + Send test error; BUG-D1 rename
immediate in GET /instances + top bar + sidebar. 89/89 tests. Both
build modes clean. Machine cleaned (pgrep -x = 0, ports free,
worktree clean @ c2cf841).

Deliverables: download/P1C3_REPORT.md + 4 evidence PNGs. Branch p1-c3
READY FOR MERGE (PR #2): 0f65b0c..c2cf841.

Next: P1-C4 (Nodes — port src-tauri/node_service.rs 554 LOC into
crates/minewrap-gui + Nodes UI + sidebar multi-node + 2-daemon E2E;
prompt DRAFT at prompts/2026-11-12-p1-chunk4-DRAFT.md — update commit
hashes + baseline 89 tests before dispatch), then P1-C5 (packaging
switch to minewrap-gui, retire src-tauri/ + ui/), then tag/release
decision (v1.10.0 still untagged; suggest tagging after P1 completes).
