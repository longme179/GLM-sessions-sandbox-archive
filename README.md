# GLM Sessions Sandbox Archive

> Nhà / trường / kho tri thức của GLM (Z.ai) qua các sessions làm việc với
> người dùng longme179 (kimhoanglong). Mọi thứ ở đây tồn tại để một session
> GLM tương lai có thể tự tái lập trong vài phút sau khi sandbox reset.

**Language rule inside this repo**: docs are English (they are for future GLM
sessions and technical precision); personal letters to self are Vietnamese.
The repo owner reads both.

## Map

| Path | What it is |
|---|---|
| `tools/` | Bridge tools to drive remote AI agents (OpenCode gateway) + GitHub API helpers |
| `skills/` | SKILL.md files — read the matching one BEFORE starting that kind of task |
| `knowledge/` | Live project state + lessons learned (UPDATE AT SESSION END) |
| `FUTURE-SELF.md` | Lời nhắn nhủ bản thân tương lai — read this first, every session |

## Quick start (fresh session, after a reset)

1. Read `FUTURE-SELF.md`, then `knowledge/lessons-learned.md` (so old pain is
   never repeated), then the skill matching today's task.
2. Credentials (OpenCode gateway URL + Basic Auth, GitHub PATs) are delivered
   by the user in the conversation/bootstrap message. NEVER store them in this
   repo — see `tools/README.md` for the env contract.
3. Export them: `export OC_URL=... OC_AUTH=user:pass` and use `tools/`.

## Update protocol (end of every work session)

- Refresh `knowledge/lme-shell-state.md` (merged PRs, open issues, runtime facts).
- Append new stories to `knowledge/lessons-learned.md` (one line of rule + context).
- Commit + push (from the user's desktop — the Z.ai sandbox IP is blocked by
   GitHub; route git through the gateway shell, see `skills/SKILL-github-pr-workflow.md`).

## Hard rules

1. No credentials in this repo. Ever. No exceptions, no "just this once".
2. No fabricated verification. If it was not verified, say so.
3. Keep tools byte-exact when transferring (base64, never let an agent paraphrase code).
