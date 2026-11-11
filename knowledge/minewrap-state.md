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

1. Phase A approved (with Q8 repo-cleanliness amendment, 2026-11-11) —
   EXECUTING. Harness master at `tools/memtest/` here; deploy to user
   machine `~/dev-memtest/` via agent (rsh.sh base64 transfer).
2. A2/A4 need the OpenCode gateway: the sandbox /tmp (where `.oc-env`
   lived) was wiped between sessions → ask the user to re-send gateway URL
   + Basic-Auth password, then re-create `~/.oc-env` (600) before driving
   the agent. GitHub PATs embedded in both repo remotes still work.
3. Branch `p0-daemon-first` + Phase B/C kickoff only after Phase A lands
   and the user sees the baseline numbers.
4. End of session: append lessons to `knowledge/lessons-learned.md`.
