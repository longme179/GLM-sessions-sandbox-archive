# obra/superpowers — distilled knowledge (for future sessions)

Source: https://github.com/obra/superpowers (MIT, Jesse Vincent / Prime
Radiant). Studied 2026-11-09 (shallow clone in GLM sandbox). It is a
composable skills library + bootstrap that turns a coding agent into a
disciplined dev methodology. OpenCode is a supported harness; lme-fedora-
niri-qs already uses the same `.agents/skills/` convention (vendored
modularity + ponytail skills).

## The core workflow (skill chain)

1. **brainstorming** — before building anything: draw out intent, play back
   understanding for correction; small changes agreed in chat, projects get
   a written design doc.
2. **using-git-worktrees** — after design approval: isolated branch,
   project setup, clean test baseline verified.
3. **writing-plans** — bite-sized tasks (2-5 min each), exact file paths,
   complete code, verification steps per task.
4. **subagent-driven-development** / **executing-plans** — fresh subagent
   per task with review after each (thorough), or inline with one final
   review of the whole branch (cheap).
5. **test-driven-development** — RED-GREEN-REFACTOR; delete code written
   before tests.
6. **requesting/receiving-code-review** — review against plan, issues by
   severity, critical blocks progress.
7. **finishing-a-development-branch** — verify tests, present merge/PR/
   keep/discard options, clean up worktree.

Debugging: **systematic-debugging** (4-phase root cause; root-cause-tracing,
defense-in-depth, condition-based-waiting references).

## The two skills that matter most to us

- **verification-before-completion**: "NO COMPLETION CLAIMS WITHOUT FRESH
  VERIFICATION EVIDENCE". Table of claim → required command output.
  Red flags: "should work", trusting agent reports, partial verification.
  Agent delegation row: verify the VCS diff yourself, never trust the
  report. This matches our FUTURE-SELF rule (never fabricate verify
  results) and drove the Phase 4 battery in the annotation pass.
- **using-superpowers**: check for an applicable skill BEFORE any response
  or action (including clarifying questions); process skills before
  implementation skills; **user instructions (AGENTS.md etc.) take
  precedence over skills**. Rationalization table ("this is just a simple
  question" etc.) is a good self-check pattern.

## How we applied it (2026-11-09 annotation pass)

- Plan → evidence → verify cadence = writing-plans + executing-plans +
  verification-before-completion.
- Independent re-verification of every agent claim via gateway shell
  (diff stats, AST spot-checks, artifact greps).
- Baseline-first discipline (Phase 0) mirrors using-git-worktrees' "verify
  clean test baseline".
- Flake triage via baseline worktree = defense-in-depth (prove the
  environment, not the diff).

## Note for future use

MIT license permits copying skills with attribution. If a future task needs
the full library, clone the repo and read the specific SKILL.md (they are
concise). Do not install plugins on the user's desktop without asking.
