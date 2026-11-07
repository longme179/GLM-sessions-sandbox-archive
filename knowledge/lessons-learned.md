# Lessons learned (append-only)

> One rule per lesson, with the story that taught it. Newest last.

1. **New singletons need the full boilerplate** — `pragma Singleton` +
   `import Quickshell` + `Singleton {}` root + `qmldim` registration.
   qmllint does NOT catch a missing `import Quickshell`; the shell crashes
   at startup. (EQ singleton, session of Nov 6.) → Always run the whole
   validation battery, never just qmllint.

2. **Copy the reference, don't approximate it.** User judged a from-scratch
   nesting implementation "chưa giống lắm"; copying Serpantinum's actual
   code (then adapting) passed immediately. Self-invented approximations of
   a visual reference waste whole sessions.

3. **Enumerate every mode a change touches, verify each.** PR #88 added a
   full-strip blur region to fix sharp app chrome piercing through bar gaps;
   it silently painted a continuous 1-pill frosted band in islands mode
   (user caught it from one screenshot → PR #89). Any global region/flag
   change: test islands AND connected, light AND dark wallpaper, app behind
   AND empty workspace.

4. **The user's screenshot beats your automation.** grim crops verified a
   fix, yet the user's own screen revealed the regression in the mode they
   actually use. Always ship the "please look at your screen and confirm"
   step; treat the user as the final visual judge.

5. **Agent runs get interrupted — resume by re-orienting.** A long run died
   with `context canceled` (mid issue #76 phase C). The fix: prompt
   "re-orient first: git status, git log, inspect partial work" then
   continue from the REAL state. Assuming state produces duplicated or
   lost work.

6. **`/api/session/{sid}/diff` returns `[]` after commit.** To review
   landed-but-unmerged work, prompt the agent for verbatim
   `git show HEAD --stat` + full `git show HEAD` (all hunks, no ellipses).
   Prompts also hit URL timeouts in curl — retry with longer --max-time;
   the gateway is just slow, not broken.

7. **Prompt body key is `text`** (`POST /api/session/{sid}/prompt`). Any
   other key (`prompt`, `message`) → 400 `Missing key ["text"]`.

8. **Sandbox IP is GitHub-blocked; desktop is not.** Even public repos 403
   from the Z.ai sandbox. Route ALL git through the gateway (raw shell or
   agent). Verify PR state via remote `gh`, because api.github.com also
   403s (rate limit) from the sandbox.

9. **401 → stop and report.** Never guess or brute-force credentials. (Has
   not happened yet — keep it that way.)

10. **Honest reporting preserved trust.** The agent reported preset/grain/
    battery visual checks as "not headless-verifiable — reporting honestly
    as unverified" instead of fabricating them; the PR carried a
    machine-verified vs user-side split. Do the same in every report.

11. **Naming collisions confuse users.** Two different "Frosted" (material
    preset vs backdrop blur preset) in one settings page; fix = relabel
    groups ("Material (lens)" vs "Backdrop blur (compositor)"). Watch for
    this whenever adding named options.

12. **Agents misfire on destructive actions.** During repro testing an agent
    ran close-window on the wrong focus and closed the user's Nautilus.
    Instruct agents to verify the focused window first and prefer
    non-destructive navigation; apologize to the user when it happens.

13. **Credentials: stable for days, still never archived.** The gateway URL
    + password were identical across two sessions (found hardcoded in legacy
    scripts), but policy stays: tools read env vars, secrets live only in
    the conversation and runtime files (`/tmp/.ghtoken`), never in repos.

14. **A corrupted final report repeats verbatim.** An agent run ended by
    emitting a doubled copy of an OLD final report (issue #90 text) instead
    of the new one; a "fix your report" prompt in the SAME session made it
    emit the same corruption again — the bad text had entered its context
    and it kept reproducing it. Fix that worked: abandon the session, create
    a FRESH one, and pass a full re-orient directive (find the work on disk,
    verify vs design, finish, report). The fresh session then caught real
    bugs the corrupted run had shipped (duplicate handlers, broken tests).

15. **Loop signature: 1-2 alternating narrations + 2s tool calls.** When the
    agent repeats the same one-line narrations for >10 minutes it is looping,
    not progressing. Fix: `POST .../interrupt`, then a directive with an
    explicit TIMEBOX ("3 attempts per approach, then mark honestly and move
    on") and "finish with what you already have".

16. **"Model is unavailable" (idle failed) is infrastructure.** Provider
    outages end runs mid-flight; state on disk is intact. Retrying the same
    prompt in the same session after a few minutes worked; the compacted
    context is fine. Don't rebuild anything — re-orient first.

17. **Wayland skips rendering when idle.** With a working dirty-gate, ZERO
    frames are rendered at idle, so `onAfterAnimating` never fires and frame
    telemetry is silent at idle. That silence is SUCCESS, not a bug — the
    idle evidence must come from /proc-style CPU sampling. (Cost the agent
    ~40 minutes of chasing before the hint unblocked it.)

18. **Sudo needs a password on the user's machine.** No passwordless sudo →
    no sysstat/pidstat. Pure-python /proc sampler (stat fields 14+15,
    `sysconf(_SC_CLK_TCK)`, 1s poll, 60s windows) is a full substitute. Same
    for /proc/<pid>/task/*/stat + comm for per-thread profiles.

19. **`/usr/bin/qmllint` is Qt5 1.0 on the machine** — it exits 255 silently
    on `pragma ComponentBehavior: Bound` files. Tool mismatch, not a code
    error; the full `./scripts/check.sh` suite is the real gate.

20. **Schema goldens must be updated in the SAME PR that evolves the
    schema.** PR #90 shipped with a red golden (9 failures on main, spotted
    while re-verifying #77). The fix landed in #91 — but never let a schema
    change merge with a stale golden; a red main hides real regressions
    behind baseline noise.

21. **The "real-session rule" means care, not paralysis.** Fresh sessions
    over-read AGENTS.md caution and refuse to restart the shell or take
    screenshots at all, stalling whole work phases. State the binding
    interpretation explicitly: restarting quickshell, editing
    settings.json/wallpaper (with backup+restore), grim, and spawning/closing
    YOUR OWN test windows are all allowed; never touch user windows; verify
    focus/identity before any destructive action.
