# Survival: direct host control when all models are down (2026-11-24)

## Situation
Mid-task, every free model on the OpenCode server started failing:
- openrouter models: `provider.invalid-request "Request path cannot be relayed"` (tunnel/relay outage)
- opencode models (tidepool, beam, mimo, hy4, deepseek): `Free usage limit reached`
Probing all 16 free models over ~25 minutes found zero working. The user then
authorized taking direct control of OpenCode and the shells.

## The escape hatch: PTY routes (no model involved)
The server (v2.3.0) exposes persistent-pty routes that run REAL shells on the
host as the host user. Full flow (see `tools/pty_run.py`):

```
POST /api/pty {"directory":"/home/kimhoanglong"}          -> data.id = pty_...
GET  /api/pty/<id>/connect   (WebSocket, Basic auth OK)   -> terminal stream
     send: raw command text; recv: raw output (first frame = 0x00+{"cursor":N})
DELETE /api/pty/<id>                                      -> cleanup
```

Route discovery trick: `GET /api/pty/write` returned
`"Expected a string starting with \"pty\" at [\"ptyID\"]"` — the router was
parsing `write` as the ptyID path segment, proving the real shape is
`/api/pty/{ptyID}/...`. Cloning sst/opencode and grepping
`packages/protocol/src/groups/pty.ts` confirmed:
`PTY_CONNECT_PATH = "/api/pty/:ptyID/connect"` (WebSocket; `ticket` query
param OPTIONAL when Basic auth is present).

## Workflow that worked
1. `pty_run.py "cmd" --clean` for each step (own PTY per command; delete after).
2. Long jobs (check.sh ~8.5 min, run-gates G0 ~8.5 min): `nohup ... > /tmp/x.log 2>&1 &`
   then poll `pgrep -f ...` + `tail /tmp/x.log` every 2-5 min.
3. File upload: `base64 -w0 local.py` in the sandbox, then
   `echo <b64> | base64 -d > /tmp/remote.py` over PTY (10 KB script = 14 KB b64, fine).
4. Multi-line python on host: `python3 - <<'PYEOF' ... PYEOF` heredoc (mind the
   apostrophe path; prefer single heredoc over nested quotes).
5. NEVER put backticks in JSON bodies passed through the host shell — the host
   bash executes them. Write JSON to a file and `--data @file`.

## Status when models die mid-implementation
- Session work (prompted sessions) keeps its file edits: they live in the repo
  working tree, NOT in the session. Stashes/pop survive.
- `git stash push -m ... -- <files>` before branching preserved the previous
  agent's WIP (see journal 2026-11-24).
- The API stays up even when providers are down; health check /api/info works.

## Re-entry checklist for the next session
1. `oc /api/info` (expect v2.3.0, fedora).
2. Read `/home/kimhoanglong/agent-collab/journal.md` (created 2026-11-24).
3. Probe models with a trivial "Reply OK" session before planning around them.
4. If all down -> direct PTY control (user pre-authorized 2026-11-24).
5. Repo: "/home/kimhoanglong/claude's works/lme-fedora-niri-qs" (apostrophe!),
   live deployment at ~/.config/quickshell/lme-shell, branch state in journal.
