# Gate 3 — 23-command UI checklist result (2026-11-11, session 7)

Run by the dispatched OpenCode agent on the real machine (session
`ses_e34e987b7ffebuYr7JsMKqNE1Z`, deepseek-v4.1-flash-free), GLM-collected
after the org-wide free-limit cut the run during wrap-up. Full raw evidence
stays on the machine at `~/dev-memtest/results/g3-checklist/` (70+ files:
per-command screenshots + REST JSON snapshots + daemon logs). This file is
the durable summary; the three overview shots are archived next to it.

Target: Tauri GUI (pure-client, P0) in worktree `~/dev-memtest/build/
Minewrap-p0-gui` @ 29e8e5f, auto-spawned sidecar daemon, scratch instance
"g3" (fakejava-echo stub extended with stop semantics + SLP responder,
port 25566, probe latency ~0.8 ms, 0/20 players, version 1.21.1).

## Verdict

**GATE 3 READY FOR MERGE: NO (yet) — 19/23 PASS, 3 UNVERIFIED, 1 partial;
2 blocking contract bugs found and already FIXED in 201675e; machine E2E
re-verification of the two fixed flows still pending.**

## Results

| # | command | how verified | result |
|---|---------|--------------|--------|
| 1 | list_nodes | by construction: sidebar "This machine — connected" routed every later command | PASS |
| 2 | add_node | not reached before model free-limit | UNVERIFIED |
| 3 | remove_node | not reached | UNVERIFIED |
| 4 | retry_node | not reached | UNVERIFIED |
| 5 | list_instances | UI + `05-list-instances.json` | PASS |
| 6 | get_snapshot | SLP probe live in UI + `07b-snapshot-running-slp.json` | PASS |
| 7 | instance_start | UI Start → Running; REST `api-start-response.txt` `{"ok":true}` (UI showed decode banner = BUG-1) | PASS* |
| 8 | instance_stop | UI Stop → Offline, no orphan stub process | PASS |
| 9 | instance_restart | full stop→start cycle, `09-snapshot-restarted.json` online | PASS |
| 10 | send_command | typed `help`, console showed `fakejava heard: help` | PASS |
| 11 | get_logs | tab-switch backfill worked in UI (REST decode hit BUG-1) | PASS* |
| 12 | get_config | Settings tab rendered scratch config | PASS |
| 13 | update_config | display-name edit → `Saved.`, disk + REST match | PASS |
| 14 | add_instance | wizard created `g3add` (daemon 201, `14-list-instances-after-add.json`); UI showed decode error = BUG-2 | PASS* |
| 15 | remove_instance | `g3add` removed via UI, workdir intact | PASS |
| 16 | detect_java | picker listed Java 21 + system default + custom | PASS |
| 17 | scan_launch | wizard Scan found the stub jar | PASS |
| 18 | read_properties | Properties tab loaded `server.properties` (see shot-c) | PASS |
| 19 | write_properties | motd edit → `motd=G3 renamed motd` on disk + REST, comments preserved | PASS |
| 20 | list_mods | both dummy jars listed | PASS |
| 21 | toggle_mod | `dummy-mod-a.jar.disabled` persisted after remount | PASS |
| 22 | discord_test | fake webhook receiver got POST; UI "Test message sent." | PASS |
| 23 | health | connected indicator green throughout; daemon-stop disconnect path not exercised | PARTIAL |

(*) = function succeeded; UI surfaced a spurious decode banner — see findings.

## Findings

1. **BUG-1 (blocking, FIXED 201675e)**: `GET /instances/{id}/logs` sends
   `LogLine.ts` as epoch-ms (`chrono ts_milliseconds`) but `LogLineDto`
   deserialized RFC3339 → "decode: error decoding response body" banner on
   every log backfill. Same class as the Slint-branch fix; now mirrored on
   p0 (Rust DTO + frontend `LogLine.ts: number` + mock adapter).
2. **BUG-2 (blocking, FIXED 201675e)**: `POST /instances` replies
   `201 {id,name}` but the client decoded `Action` → decode error in the
   wizard although the instance WAS created. 201 body now mapped explicitly.
3. **Finding-3 (build, open)**: the worktree release binary again showed the
   "Could not connect to localhost" WebKit page (stale build with empty
   ui/dist at compile time — lesson #76.3). Workaround used: local
   http.server on :5173. Final merge verification must build through
   `./build.sh` (already E2E-tested in session 5).
4. **Stub hardening (harness-side)**: bash background jobs get /dev/null
   stdin, so the stub never saw `stop`; fixed with an explicit stdin pipe +
   SLP responder. Fakejava-echo now supports lifecycle + SLP + echo commands.

## Machine state after cleanup (GLM-verified via raw shell)

Our GUI/daemon/fakejava/webhook-receiver/http.server killed by exact PID;
user's real AppImage app (PID 2603173 + its WebKit children) untouched and
alive; both checkouts clean (`?? binaries/` pre-existing sidecar staging in
the -gui worktree only).

## Vision cross-check (GLM, 3/3 RENDER-OK)

- shot-overview-a/b: console tab, G3 Scratch online 0/20 · 1.21.1, ring
  186/186 → 190/190, 4 level colors (ERROR red / WARN yellow / INFO white /
  DEBUG gray), sidebar "This machine — connected", no defects.
- shot-overview-c (from the #19 flow): Properties tab, raw textarea with
  comments preserved, `motd=G3 renamed motd`, Reload/Save present.
