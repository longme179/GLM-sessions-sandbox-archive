# tools/ — bridge to remote AI agents & GitHub

All tools read credentials from the environment. Nothing is hardcoded.

```bash
export OC_URL="https://<gateway-host>"        # OpenCode gateway base URL
export OC_AUTH="user:pass"                    # Basic Auth (opencode:<password>)
export OC_SID="ses_..."                       # active session id (some tools)
export GH_TOKEN_FILE=/tmp/.ghtoken            # for gh_pr.py (write-only, never commit)
```

The user supplies these values in each session's bootstrap message. Never
echo them into files, commits, issues, PRs, or this archive.

| Tool | Channel | Use |
|---|---|---|
| `qw.py sh "cmd" [sec]` | `POST /api/shell` + `/output` paging (pure python, no curl) | Same job as `rsh.sh` but works in sandboxes WITHOUT curl (the Qwen sandbox). Also `qw.py sessions/new/prompt/msgs/wait/api`. Reads `OC_URL` + `OC_AUTH` (raw `user:pass`). |
| `rsh.sh "cmd"` | `POST /api/shell` (global, session-less) | Run one raw shell command on the user's desktop; prints full output. Best for git & file transfer. |
| `oc.py new` / `run` / `bg` / `poll` | `POST /api/session/$OC_SID/shell` | Session-scoped shell: create sessions, run tagged commands, background jobs with log polling (`OCJOB_DONE`). |
| `oc_prompt.py <sid> <file>` | `POST /api/session/{sid}/prompt` | Send a task prompt (body key is **`text`**) to the coding agent. |
| `oc_report.py <sid> ...` | `GET /api/session/{sid}/message` | Read agent progress: `tail`, `report` (final long text), `trace` (tool calls), `wait` (block until `idle`). |
| `oc_fetch.py <sid> <remote> <local>` | session shell, chunked base64 | Pull a file from the desktop byte-exactly (screenshots, artifacts). |
| `gh_pr.py --repo ... --head ...` | GitHub REST API | Create (and optionally immediately merge) a PR; token from `--token-file` (default `/tmp/.ghtoken`). |

## Channel map (discovered 2026-11, gateway OpenAPI)

- `POST /api/session` `{"location":{"directory":"/home/kimhoanglong"}}` → `data.id`
- `POST /api/session/{sid}/prompt` — body `{"text": "..."}` (NOT `prompt`/`message`; wrong key → 400 `Missing key ["text"]`)
- `GET  /api/session/{sid}/message?take=N` — reverse-chronological; reverse it for chronological order
- `POST /api/session/{sid}/wait`, `GET /api/session/{sid}/diff` (returns `[]` once changes are committed — ask the agent for verbatim `git show` instead)
- `POST /api/session/{sid}/shell` `{"command": ...}` — result appears as a message `type=="shell"` with `status=="exited"` and `output.output`; visible to the agent, avoid in live agent sessions
- `POST /api/shell` `{"command": ..., "timeout": ms}` (global, agent-free) → `data.id`; `GET /api/shell/{id}` (status); `GET /api/shell/{id}/output?cursor=&limit=` (incremental)
- End of an agent run: a message `{"type":"idle","outcome":"succeeded"|"failed"|"interrupted"}`; the long final assistant text (>= 300 chars) is the report; short lines are progress narration.

## oc.sh + oc-poll.sh (added Q4, 2026-11-10)

Thin curl wrappers for the OpenCode gateway API. Credentials NEVER live in
these files: both source `${OC_ENV:-$HOME/.oc-env}` (chmod 600) which must
define `OC_URL`, `OC_AUTH` (the full `Authorization: Basic ...` header value)
and optionally `OC_SID` (the active session id — VERIFY it before prompting;
a stale id silently sends tasks to the wrong session).

- `oc.sh models|agents|info` — read-only listings.
- `oc.sh new DIR` — create a session (prints the id; append it to the env file).
- `oc.sh set-model provider/model` — switch (Model.Ref object form; Q4 default
  `opencode/deepseek-v4.1-flash`, fallback `-free` variant on 402 quota).
- `oc.sh prompt TEXT` — send a task (`$(cat file)` for long prompts).
- `oc.sh wait [SEC]` — block until the current run finishes.
- `oc.sh msgs` — message list (plain array or `{messages:[...]}`).
- `oc.sh abort` — interrupt the current run.
- `oc-poll.sh AFTER_TIMESTAMP [TIMEOUT]` — poll until a new assistant
  `finish=stop` message appears after the given epoch-ms timestamp; prints
  the final report. Get the timestamp from the last user message before
  your prompt (`oc.sh msgs`).

## qw.py (added 2026-11-11, Qwen handover session)

Pure-python bridge for sandboxes where `curl` is not installed (the curl-based
`oc.sh` / `rsh.sh` wrappers fail there with "curl: command not found").

```bash
export OC_URL=... OC_AUTH='opencode:<password>'
python3 tools/qw.py sessions                 # id / updated / outcome / title
python3 tools/qw.py sh 'git -C ~/repo log --oneline -3' 90
python3 tools/qw.py new /home/kimhoanglong   # create a session
python3 tools/qw.py prompt <sid> task.txt    # body key is "text"
python3 tools/qw.py msgs <sid> 6             # chronological tail
python3 tools/qw.py wait <sid> 600           # block until idle
python3 tools/qw.py api GET /api/model
```

Notes: `sh` submits to the global agent-free shell and pages `/output` by
cursor, so long outputs are not truncated; it prints `[status=... exit=N]`.
Guard empty variables in remote one-liners — a failed `$(grep -l ...)` once
turned `dirname ""` into `.` and listed the owner's home (lesson #77.7).
- `oc-shell.sh` — global /api/shell executor (no agent session); auth via a
  600-mode `Authorization: Basic ...` header file (`curl --header @file`)
  because `curl -K` breaks on some hosts (curl 8.14.1). Env: OC_URL, OC_HDR,
  OC_CWD. Polls to exit + wall grace, mirrors rsh.sh with portable auth.

## Agent-1 session tools (2026-11-14 → era, lessons 83/84)

| Tool | Use |
|---|---|
| `dump_agent1_tail.py <sid> [N]` | Chronological tail of a session's last N messages (ids + timestamps + text, truncated at 6000 chars/message). Poll with this. |
| `oc_get_message.py <sid> <msg_id>...` | FULL text of specific message ids (when the tail truncates). Auth via `/tmp/oc_auth`. |
| `find_agent1_session.py` / `scan_agent1_sessions.py` | Discover session ids by activity/title. |
| `pull_remote_file.sh <remote> <local> <size> <md5>` | Chunked pull of files > 45 KB through the bridge (dd bs=30000 \| base64 per chunk, reassemble, md5-gate). |

**Auth bridge rebuild (every turn — /tmp is recycled between TURNS):**

```bash
source /home/z/my-project/scripts/oc_env.sh && export OC_URL OC_AUTH
python3 -c "
import base64
hdr = 'Authorization: Basic ' + base64.b64encode('$OC_AUTH'.encode()).decode()
open('/tmp/oc_auth','w').write(hdr + '\n')"
```

(The sandbox keeps credentials in `scripts/oc_env.sh` — NEVER copy that file
into this archive; the template above is the contract.)

**Hard limits (measured 2026-11-15):**

- oc.sh response cap: **exactly 49152 bytes, silent truncation** — anything
  larger must go through `pull_remote_file.sh` chunks or a remote-generated
  thumbnail. PIL opening a truncated PNG proves nothing.
- `~` inside single quotes does not expand through the bridge — always use
  absolute remote paths (`/home/kimhoanglong/...`).
- Gate verdicts: read the G*.json the run produced (`returncode`, counts);
  `run-gates.sh` exits 1 on "completed-with-skips" while the gate passed.
