# SKILL: driving a remote OpenCode coding agent

Use this skill whenever work must happen on the user's machines (their shell
repo, their desktop state) — GLM's own sandbox usually cannot reach GitHub
(IP-blocked) and must not touch the user's machine directly. Everything goes
through the OpenCode gateway; credentials arrive in the session bootstrap
message (Basic Auth `opencode:<password>` + gateway URL). 401 → stop and
report. Never store or echo credentials.

## Mental model

- The gateway hosts OpenCode (a coding agent) with an HTTP API. Sessions are
  scoped to a directory (`/home/kimhoanglong` = the user's home).
- TWO channels exist:
  1. **Agent channel** — for tasks requiring intelligence (implement, debug,
     validate, take screenshots). Prompt-driven, asynchronous, narrated.
  2. **Raw shell channel** — `POST /api/shell` (global, agent-free) or
     `POST /api/session/{sid}/shell` (session-scoped; results become session
     messages, so the agent SEES them — avoid in live agent sessions). Use
     for git, file transfer (base64), quick probes.
- Tools live in this repo under `tools/` (see `tools/README.md`).

## Agent-channel protocol (proven across PRs #73–#125)

1. `POST /api/session` → `data.id`; reuse one session per topic.
2. `POST /api/session/{sid}/prompt` with body `{"text": ...}` — the key is
   **`text`**; anything else → 400 `Missing key ["text"]`.
3. Completion = a message `{"type":"idle","outcome":...}`. While working the
   agent emits short narration lines; the final report is the last text
   >= ~300 chars. Use `tools/oc_report.py <sid> wait` to block on it.
4. `GET /api/session/{sid}/diff` returns `[]` after changes are committed —
   for review, prompt: "output `git show HEAD --stat` then the full `git show
   HEAD` diff verbatim, all hunks, no truncation".

### Model selection & switching (Q4 lessons, 2026-11-10)

- List: `GET /api/model` → `data` is a flat array of
  `{id, modelID, providerID, ...}`. The owner's preferred model is
  **`opencode/deepseek-v4.1-flash`** (family `deepseek-flash`).
- Switch: `POST /api/session/{sid}/model` with
  `{"model":{"id":"deepseek-v4.1-flash","providerID":"opencode"}}` — a
  Model.Ref **object**; a plain string 400s with "Expected Model.Ref".
- Rate limit/quota: the paid variant can 402 "Insufficient balance";
  switch to the same model's free variant (`opencode/deepseek-v4.1-flash-free`)
  — same family, same tool quality, worked all round.
- Session hygiene: copy session ids FULL-LENGTH (truncating →
  SessionNotFoundError); keep the active id in a local env file
  (`~/.oc-env`, chmod 600, sourced by the helper scripts) and VERIFY which
  session a prompt landed in before waiting — a stale id silently sends the
  task elsewhere (recover with `POST /api/session/{sid}/interrupt`, returns
  `{"interrupted":true}`). Reuse one verify session across rounds: it
  remembers its worktree/venv/pointer setup; just `reset --hard` the worktree.
- Message list: `GET /api/session/{sid}/message` returns `data` as a plain
  array (older builds wrapped `{messages:[...]}`) — parse both. Progress =
  assistant messages with `finish:"tool-calls"`; done = `finish:"stop"`;
  failures show `finish:"error"` + `error.type` (e.g. `provider.quota`).

### Prompt patterns that worked (keep using them)

- **Design-first**: scope discovery prompt → wait for the map (issue quote,
  current-state audit, done-vs-missing, plan) → approve a binding design →
  implement. Never let the agent freestyle a design it invented itself.
- **Numbered steps with measurable success criteria**: "screenshot X must
  show Y"; "no sharp pierce"; "validation battery all green".
- **STOP-gates**: "STOP before PR: report diff verbatim + validation outputs
  + screenshot findings. I will review, then authorize PR + merge." This is
  the review-gate that keeps GLM in control of what lands on main.
- **Resume after interrupt** (runs die with `context canceled` — normal):
  first prompt = re-orient (`git status`, `git log --oneline`, inspect
  partial work), then continue from the actual state, never assumed state.
- **Credentials**: pass the GitHub PAT only as
  `printf %s\\n "<token>" | gh auth login --with-token` inside a prompt;
  require the agent to confirm "token never written to any file or output".
- **Honesty clause**: require the agent to report unverified items as
  unverified ("machine-verified vs user-side remaining") — never let it
  fabricate verification results.

### Known failure modes (all seen live)

- Agent closes the wrong window while testing (closed the user's Nautilus
  once) → instruct it to verify the focused window before destructive
  actions, prefer non-destructive navigation.
- Over-correction fixes the reported symptom but regresses another mode
  (fullStrip band fixed gap-pierce, broke islands) → always enumerate the
  style/mode variants a change touches and verify each.
- Agents rename or relabel on their own initiative — good when it resolves a
  real collision (two "Frosted" meanings), but require them to flag it.

## Raw-shell protocol

- Global: `POST /api/shell` `{"command": "...", "timeout": ms}` → `data.id`;
  `GET /api/shell/{id}` until `status` in done/error/exited;
  `GET /api/shell/{id}/output?cursor=N&limit=2000000` (incremental; keep
  paging while `cursor` grows). Wrapped by `tools/rsh.sh`.
- File transfer MUST be byte-exact: `printf %s <base64> | base64 -d > path`
  per file, then compare `wc -c` against the local original. Never let the
  agent retype file contents from a prompt.
- Fetch direction (desktop → sandbox): `tools/oc_fetch.py` (chunked base64
  through session shell + inbox).
