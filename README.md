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
| `knowledge/` | Live project state + lessons learned (UPDATE AT SESSION END) + dependency capability snapshots (`niri.md`, `quickshell.md`) |
| `knowledge/a4-active-state.md` | CURRENT era read-first file (Agent-1/Agent-2 collaboration, PRs #168–#171, owner live checklist pending) |
| `journal/` | Snapshots of the collaboration journal (`~/agent-collab/journal.md` on the owner's machine) — the evidence backbone |
| `plans/` | Numeric plans as executed (A4c c2-c3 fixes, island morph, polish, closeout runbook, lock port) |
| `FUTURE-SELF.md` | Lời nhắn nhủ bản thân tương lai — read this first, every session |

## Quick start (fresh session, after a reset)

1. Read `FUTURE-SELF.md`, then `knowledge/a4-active-state.md` (the current
   era), then `knowledge/lessons-learned.md` — INCLUDING the `[RETIRED]` /
   `[OVERTURNED]` marks (wrong lessons are marked at the place they live,
   with the evidence that killed them; do not re-learn them), then the skill
   matching today's task. If the task touches an external dependency (niri,
   quickshell, …), read its snapshot under `knowledge/` too; if stale or
   missing, refresh it FIRST with `skills/SKILL-codebase-docs-updater.md` —
   never design from memory.
2. Credentials (OpenCode gateway URL + Basic Auth, GitHub PATs) are delivered
   by the user in the conversation/bootstrap message. NEVER store them in this
   repo — see `tools/README.md` for the env contract.
3. Export them: `export OC_URL=... OC_AUTH=user:pass` and use `tools/`. The
   sandbox recycles /tmp between TURNS — rebuild the auth bridge every turn
   (lesson 84.7).

## Update protocol (end of every work session)

- Refresh `knowledge/lme-shell-state.md` (merged PRs, open issues, runtime facts).
- Append new stories to `knowledge/lessons-learned.md` (one line of rule + context).
- Commit + push (sandbox → GitHub over HTTPS+PAT works since 2026-11-07 —
   lesson 30; the gateway-shell route in `skills/SKILL-github-pr-workflow.md`
   stays as fallback).

## Hard rules

1. No credentials in this repo. Ever. No exceptions, no "just this once".
2. No fabricated verification. If it was not verified, say so.
3. Keep tools byte-exact when transferring (base64, never let an agent paraphrase code).
