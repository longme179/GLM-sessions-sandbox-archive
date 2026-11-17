# SKILL: orchestrating a small local agent through the OpenCode HTTP gateway

Learned/refined 2026-11-16 (iNiR→LME port analysis session). Builds on
`SKILL-remote-opencode.md` (keep reading that first for the channel map).

## Division of labor that worked
- **Strong model does the analysis**: clone repos LOCALLY in the sandbox (same pinned
  commits as the machine-side clones), read framing docs yourself, fan out read-only
  Explore subagents for per-area inventories with `path:line` citations, synthesize.
  The small agent (ernie-5.5-flash) is unreliable for open-ended code analysis but
  excellent at literal, numbered, self-contained step lists.
- **Small agent does the machine**: setup/clone/meta tasks (T01-style), machine facts
  (T02-style: rpm -q, lspci, command -v lists, read-only git status of the live
  checkout), and verification (T03-style: "run these exact sed commands, reply
  OK/MISMATCH per label").
- Byte-exact file delivery: write files in the sandbox, upload via base64 chunks with
  md5 gate (`tools/oc2.py put`); never ask the small agent to retype content.

## Prompt pattern for a flash-class agent (all worked first try)
```
[TASK Tnn] <short title>
CONTEXT: 2 sentences, working dir, hard rules (read-only, no install/setup scripts,
never launch shells, no sudo), what NOT to touch.
GOAL: one sentence.
STEPS: 1..N exact commands with absolute paths; "If a step fails, append the exact
error to <logs file> and stop. Do not guess or work around."
OUTPUT: exact file path + exact structure skeleton (headings/fields).
REPLY: ONLY "STATUS=done|blocked", "FILES=...", 3 bullets max. Do not paste file contents.
```
- ~8-10 steps per task is the sweet spot; more than that, split the task.
- Always give the JSON skeleton verbatim for structured outputs — flash models copy
  structure well.
- Verify-kép: re-read every produced file yourself through the shell channel (md5 +
  cat); never trust the agent's "done".

## Completion detection & polling (gateway v2.2.6)
- `GET /api/session/{sid}` → `data.time`: idle > busy means the turn is done; outcome
  field gives succeeded/failed. Poll every 10s inside one dispatch call (oc2.py
  `dispatch <file> [timeout]` = send + wait + print final assistant text).
- Final report = last assistant message with non-empty text content
  (`content[].type=="text"`); reasoning parts are separate.
- Background dispatches: run `oc2.py dispatch` with `run_in_background` and read the
  output file when the notification arrives — lets sandbox work continue in parallel.

## Traps (this session)
- `command -v qsb` misses /usr/lib64/qt6/bin/qsb — tool-presence checks must know
  non-PATH locations (ask for `rpm -q <pkg>` as backup).
- The mission brief can be stale (iNiR "v2.30 + patches/quickshell" was actually
  v3.1.1 + prebuilt qs-rs runtime). Verify every background fact against the clone
  before building on it; record corrections under Assumptions.
- Secret-lint word lists hit harmless words ("password" in PAM context) — review hits
  manually instead of aborting blindly.
- iNiR-family repos: check `SystemInfo.runtimeHas(...)` feature probes — features that
  need the qs-rs runtime (ScreencopyView `niriWindowId`/`sourceRect`) do NOT exist in
  stock Quickshell 0.3.2 and must be flagged non-portable.

## Files
- `tools/oc2.py` — this session's bridge (status/sh/dispatch/wait/last/put with md5 gate).
  Env: OC_URL, OC_AUTH, OC_SID (see `tools/README.md`; credentials never in this repo).
