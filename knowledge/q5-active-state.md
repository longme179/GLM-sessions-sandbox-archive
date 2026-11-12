# Q5 ACTIVE STATE — read this FIRST on any new session

Last updated: 2026-11-12 (session that started Q5)
Owner approved Q5 on 2026-11-12: "duyệt Q5 (weather, lyrics, wallpaper, file search,
equalizer, clipboard — fileOpen cũng chuyển theo entry search của Q5)".

## If you are a new session resuming this work

1. `cd /home/z/my-project/repos/lme-fedora-niri-qs && git fetch origin -q && git log --oneline origin/main -8` — which PRs are merged.
2. Read `docs/QML_FIRST_MIGRATION_PLAN.md` §5 Q5 + status line 3, `docs/STATE.md`, `docs/MIGRATION_LOG.md` heads.
3. Read `/home/z/my-project/repos/GLM-sessions-sandbox-archive/knowledge/lme-shell-state.md` tail + `lessons-learned.md` (69-74).
4. Continue the first unfinished item below. Do not re-plan; do not ask questions; repo rules forbid self-merging (owner merges PRs).

## Current status (update as work lands)

- [x] Q4 closed via PR #128 (qml/q4-closeout — capture/recording backend-fed transitional +
      banded strength compare; awaiting owner merge at session start — CHECK merge state first).
- [ ] BUG (owner-reported, authorized): Liquid Glass OFF + Materials UI, blur-behind-popups
      ON: first popup open is fine; close + reopen → blur layer covers the whole screen
      (murky). Repro loop + fix on its own branch (fix/glass-blur-reopen or similar).
- [ ] Q5 leg 1: TBD after family inventory (see plan §5 Q5 + scripts/ families).
- [ ] Q5 leg 2: TBD.
- [ ] Q5 leg 3: TBD.
- [ ] Q5 close-out: live checklist + docs + archive records.

## Standing rules (owner, 2026-11-12)

- Sub-agent prompts ALWAYS in English. Provider preference: opencode > openrouter;
  free models in order: deepseek-v4.1-flash-free > nemotron-3-ultra-free
  (GET /api/model for exact ids; paid variants 402). Budget 2x1000 free calls/day.
- Remote machine files: consolidated under ~/glm-work/ ONLY; sweep /tmp strays
  (lme-*, q4-*) when seen. Live shell never killed by us (owner restarts post-merge).
- Sandbox-side: everything under /home/z/my-project/ (scripts in scripts/, repos in repos/).
- OpenCode auth: /home/z/my-project/.oc-auth.b64 (chmod 600; curl --header @file —
  curl -K breaks). Executor: bash scripts/oc.sh <timeout_ms> <command>.
- Never print/commit credentials.

## Q5 scope notes

Families per plan §5 Q5: weather, lyrics, wallpaper (gowall chain), file search,
equalizer, clipboard; fileOpen moves with Q5's search entries. Discipline: per-leg
branch qml/q5-*, tests→impl→docs, PINNED_MESSAGES, REL/INVARIANT/GOTCHA comments,
ratchets up only (line-sed architecture.json), .pragma library JS, pragma Singleton
QML + qmldir, DEPRECATED(Q5->Q6) markers, engine cases for every protocol write,
contracts pin call shapes. A cron/scheduler was requested but the z.ai session has no
cron tool — this file is the resume mechanism instead (sync a copy to the archive repo
as knowledge/q5-active-state.md and keep both updated as legs land).
