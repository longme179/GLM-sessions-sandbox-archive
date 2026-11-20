# A4c/Tier-A ACTIVE STATE — read this FIRST on any new session

> **UPDATE 2026-11-20: this era is closed.** Roadmap closed 100% on
> 2026-11-01; the post-roadmap hardening series (a4c fixes, PB-31..PB-35)
> is fully merged — last was PR #176 (flameshot) — main `1f0880c`. Read
> `sessions/2026-11-20-pb35-closeout-end4pC-analysis.md` and the
> "Session 2026-11-20" section of `knowledge/lme-shell-state.md` instead.
> Everything below is history (A4c/Tier-A era).

Last updated: 2026-11-15 ~23:45 +07 (Agent-2 session: c2c3 closeout + verify-kép + deploy).
Supersedes q5-active-state.md (Q5/Q6 closed long ago — kept for history).

## Where things stand (one paragraph)

All four c2c3 fix PRs are MERGED (#168 idle first-enable, #169 capture export,
#170 clipboard focus, #171 suspend native — merged 22:35-22:36+07) and DEPLOYED
(main `7bc362d`; deploy 23:24, shell PID 1621529, backend 1621546; md5-verified
repo == live for all 6 changed files; smoke green: panel toggle, clipboard state,
lock=unlocked, no new log errors). The G4 gate that diagnosed the C2 failures now
runs **35/35** (was 24/35), G0 **1291/0/190** (1481 ran). The ONLY thing between us
and closing the Tier-A item "G4 env diagnose + LME_TEST_POINTER, L2 live test" is
the owner's ~5-8 min live checklist (below) + the OQ-5 decision.

## Pending on the OWNER (the very next actions)

1. **Live checklist (needs them at the machine):**
   - Suspend from PowerMenu → must see the NATIVE lock (not swaylock); resume
     unlocks (PR #171, security path — escape hatch: swaylock fallback still exists).
   - Enable idle with a short timeout, FIRST enable after boot → `lock status`
     shows running immediately, no stall (PR #168 F1).
   - Capture editor: Save PNG / Copy image / Extract text (PR #169 — MANDATORY:
     AnnotationCanvas is a product change).
   - Clipboard: right-click an image → preview; Back has focus; Escape returns
     focus to search, typing immediately loses no characters (PR #170).
   - §6 d/e of A4c: Settings → disable animations → island snaps to 28/15 instantly;
     motionSpeed 2 → visibly 2× faster (recipe in reports/a4c-closeout-status.md;
     restore prefs after).
2. **OQ-5 decision**: replace `~/glm-work/tests-local` with the final local test set
   (at `/tmp/opencode/a4c-fix/local-tests-final` + uncommitted in the integration
   worktree; includes ratchet updates test_capture_night 362→366, test_clipboard
   252→259) — or keep it separate. Agent-1 chose the conservative option (NOT
   overwriting) until the owner picks.
3. After both: Agent-1 writes the closing journal entry; Tier-A item closes;
   ROADMAP Tier A continues: **A3 FadeLoader → A5 wallpaper → A6 StyledTextChange**.

## Key machine facts (verified this session)

- Live shell = repo via symlink: `~/.config/quickshell/lme-shell →
  ~/lme-fedora-niri-qs` (deploy "0 file changes" is NORMAL; niri kdl fragment is
  the exception). Quickshell auto-reloads on git pull — backend respawns under the
  same shell PID (NOT a crash).
- Shell PID 1621529, backend 1621546 (post-deploy restart 23:27+07).
- Worktrees: `~/lme-worktrees/a4c-{clipboard,capture-fixture,suspend-native,
  idle-first-enable,c2c3-integration}` (integration @ d27ad71 = the 4 PRs merged;
  local tests + ratchets uncommitted inside each).
- G4 recipe (pointer + env): `~/glm-work/lme-pointer/` + `--env-file
  ~/glm-work/lme-pointer/env.sh --pointer-dir ~/glm-work/lme-pointer` (from
  reports/g4-env-diagnose.md).
- Known-good baselines: G1 = 6 pass / 3 audio-availability failures (same 3 names
  in 5 prior main-baseline runs — environmental, NOT a regression);
  `backend_reconnect` flaky by machine state (green in some runs).
- Collaboration journal (the source of truth): `~/agent-collab/journal.md` on the
  owner's machine (snapshot in this repo: journal/agent-collab-journal-2026-11-15.md,
  md5 da49e64f at pull time). Plans in `~/agent-collab/plans/`, reports in
  `~/agent-collab/reports/`, evidence PNGs `~/agent-collab/artifacts/`.

## The Agent-1 / Agent-2 protocol (as operating since PR #164)

- Agent-1 = the OpenCode agent on the owner's machine, one long-lived session
  (`ses_e2cc73b20ffeBwzyf76e22dwdy`). The owner ALSO talks to it directly (their
  machine, their terminal) — always re-read the journal tail + `gh pr list` before
  assuming what happened.
- Agent-2 (GLM, this sandbox) = orchestrator + independent verifier: writes numeric
  plans, steers Agent-1 through the oc.sh bridge, then VERIFIES KÉP — never trust
  the implementer's report: rerun the gates, re-diff against the plan, check
  caps/ratchets/isolation yourself.
- Steer pattern: Write the directive to a file → `oc_prompt.py <sid> <file>` →
  poll `dump_agent1_tail.py <sid> N` + `gh pr list` in ~2-4 min sleeps → verify →
  journal entry (append via base64 through the bridge) → report to owner.
- Journal discipline: every significant action gets an entry (who, what, evidence
  path, limits kept). Agent-1 writes theirs; Agent-2 writes its own verify/orchestrate
  entries. Never merge into one voice.
- PR convention (#166/#167 style): body = purpose, source finding, diff stat,
  RED→GREEN evidence path, caps, integration verification, reviewer triage,
  explicit "Owner live check" section. Owner merges (or Agent-1 after explicit
  owner go-ahead); Agent-2 never self-merges.
- Limits that held all week: no live suspend/lock/idle actions in tests (tripwire
  pattern, lesson 84.4); tests/ untracked (policy PR #136); no credential ever
  in the journal/repo; G0/G4 verdicts read from the gate JSON, not the runner
  exit code (lesson 84.5).

## Deferred / known-open (not blockers)

- Review Minors 6/7/9 from the c2c3 review round (no repro, cost-if-wrong recorded
  in the SDD ledger: knowledge/reports/a4c-sdd-ledger-2026-11-15.md).
- G4 disposable-env failures (editor window timeout, clipboard watcher/withdrawal)
  — pre-existing in the disposable sway env, out of scope of the fixes; follow-up
  noted in reports (from the #156 verify round, Nov 14).
- This GLM model line has no image input; visual judgments are the owner's (or
  VLM's) job. PNG evidence lives on the owner's machine under
  `~/agent-collab/artifacts/`.
