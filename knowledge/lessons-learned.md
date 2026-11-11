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

22. **The OpenCode gateway message pipeline silently drops short bracket
    fragments** (e.g. `[m`) in message text, BOTH directions: an agent's
    "verbatim" diff showed `Theme.glassControlsodelData]` where the real file
    has `Theme.glassControls[modelData]`, and even my own prompt echoed back
    through the API was mangled the same way. NEVER trust verbatim diffs in
    agent messages for syntax-level review — verify against the real file with
    mangling-proof probes (`grep -c 'pattern['`, `sed | base64`) before
    approving. This is why the #93 STOP-gate caught nothing on its own.

23. **`/api/shell` (rsh) kills the whole process tree when the HTTP call
    times out.** `lme-shell start` does a FOREGROUND `exec quickshell`
    (start.sh:110), so a restart issued directly via rsh leaves the new shell
    as a child of the gateway bash — and it gets killed minutes later when the
    call times out, leaving the desktop with NO bar. Recovery + prevention:
    start with `setsid nohup ~/.local/bin/lme-shell start >/dev/null 2>&1 <
    /dev/null &` (the launcher PID becomes quickshell via exec, in its own
    session — survives). Verify with `pgrep -x quickshell` + pixel-diff of the
    top strip against a dead-state screenshot (bar present = ~30k colors and
    high variance vs wallpaper-only ~14k). Better: delegate restarts to the
    agent session's own bash tool, which does not tree-kill.

24. **`pgrep -f` self-matches the gateway's `bash -c` wrapper** (the probe's
    own cmdline contains the pattern) — every "PID changed between checks"
    scare during the #93 restart was a self-match. Use `pgrep -x <exact name>`
    or add `| grep -v bash` and sanity-check the printed cmdline.

25. **OpenCode message streaming race in waiters:** an assistant message read
    mid-stream has incomplete content — a final marker appended seconds later
    is missed if the waiter caches messages as "checked". oc_wait exited
    "idle, no marker" while the agent was still streaming; the report DID end
    with the marker. Fix: always re-check the ~3 most recent messages every
    poll (sandbox scripts/oc_wait2.py has it; archive tools/oc_* still old —
    port the fix when touching the archive).

26. **GitHub sub-issue linkage was never recorded on epic #72**, so closing
    the last sub-issue #78 would NOT auto-close the epic. The final PR had to
    say `Closes #72` explicitly (verified all sub-issues closed first). For
    any epic: check the linkage fields BEFORE the closing PR and add explicit
    closes as needed — or the epic lingers open forever.

27. **The "xray" complaint was the yield cap, not niri config.** The user
    swore glass "x-rayed" the desktop background through windows. Config
    was verified perfect (niri 26.04, xray-false rules included last,
    appliedBlur true, all runtime gates true via GLASSDBG logging) and an
    A/B kill+restart changed NOTHING — determinism proved it was not
    staleness. Root cause: the shader's yield branch capped its tint at
    0.15/0.22 and ignored Panel tint opacity, so True-backdrop glass was
    ~85% see-through and the blurred backdrop stayed recognizable. Fix =
    feed Theme.panelOpacity in as a yieldOpacity uniform (PR #95). When a
    visual complaint comes with perfect config, measure the RENDERED pixels
    (correlation vs wallpaper/browser references) before blaming config or
    staleness.

28. **VLM + Pearson correlation on the user's own screenshots is the
    discriminator for "what does the glass show".** Correlation of a glass
    region against the same-region wallpaper (raw + GaussianBlur(12)x2)
    settles wallpaper-vs-browser objectively; three traps: correlation is
    invariant to tint (structure only — a 0.91-corr bar strip can still be
    correctly tinted), settings-page content dominates the stats (pick
    sparse areas like the Night Light page, or the VLM for structure), and
    the wallpaper may have CHANGED between screenshots (shuffle playlist!) —
    use the wallpaper FILE plus a fresh grim for ground truth, not old
    screenshots. Single VLM calls can also hallucinate (first call "saw"
    browser images that a comparative 2-image call disproved) — prefer the
    multi-image comparative prompt.

29. **`~/.config/lme-shell/settings.json.bak-*` files are a free changelog
    of what the user was fighting.** Diffing the Nov 6 backup showed
    opacity 0.2→1.0, a tint change and appliedBlur appearing: the user had
    been cranking Panel tint opacity for a day trying to de-xray the glass
    before reporting it. Check the backups before designing the fix — they
    tell you which knob the user already tried.

30. **Sandbox→GitHub push over HTTPS+PAT WORKS now (2026-11-07).** Lesson 8
    is outdated for git: `git push https://x-access-token:<PAT>@github.com/...`
    from the Z.ai sandbox succeeded (previously only reads worked). Still
    verify with a PAT-authenticated curl because unauthenticated
    api.github.com calls can rate-limit. AND: the gateway truncates very
    large prompts (~40KB) mid-base64 — the agent "auto-padded" truncated
    base64 into silently shorter files (5407/9139 bytes landed). For file
    transfers through prompts keep each prompt ≤ ~12KB, or verify landed
    byte sizes against the source before trusting the transfer.

31. **When a visual bug survives a parameter-level fix, suspect the
    architecture, not the parameters.** PR #95 tuned the yield tint and
    measured correlation 0.55→0.05 — yet the user still saw the background
    and escalated: "I don't want the glass shader to take ANY information
    about the desktop background. Don't overcomplicate things." The real
    fix (PR #96) was deletion: the entire wallpaper-sampling lens
    (GlassBackdrop snapshot → shader sampler) went away, 221→95 frag lines,
    -736 lines net. The user had diagnosed the architecture better than
    the fixes did. Ask "which layer SHOULD own this effect?" before
    patching constants in the wrong layer.

32. **The old-idle trap in gateway waiters.** After POSTing a new prompt,
    the last `idle` message in the session is still from the PREVIOUS run
    — a naive waiter exits instantly "success" while the new run is still
    working. Fix: only accept idles with a timestamp NEWER than the prompt
    message (scripts/oc_wait2.py takes the prompt epoch-ms as arg). Also
    re-check the last ~3 messages each poll for the streaming race
    (lesson 25).

33. **The agent backgrounds long commands and goes idle without
    reporting.** Twice it launched `./scripts/check.sh ... &` (2.5 min),
    narrated one line, and ended the run "succeeded" — no report. Don't
    prompt it to wait; just sleep the expected duration and read the log
    directly through the raw-shell channel (rsh), which is cheaper and
    mangling-proof.

34. **VLM verdicts about "what is behind the glass" need geometry
    awareness.** The VLM swore the bar pills painted a "stale wallpaper
    copy" because they showed sky while a magenta window filled the
    screen — but the bar reserves an exclusive zone, so the magenta window
    starts BELOW the bar; blurred wallpaper sky behind the pills was
    CORRECT. Ten lines of PIL hue statistics (magentaFrac 0.000 in the
    pill strip, transition at y≈30/506) settled what the VLM asserted
    wrongly. Layer-shell exclusive zones mean "content behind a bar" is
    usually wallpaper, not windows — check before believing a "stale
    snapshot" verdict.

35. **Grep-proofs + byte-exact file fetch beat narrative review.** For the
    #96 review gate: sha256-matched base64 fetch of the frag (read every
    line myself), grep counts (0 sampler2D / 0 GlassBackdrop / 0
    glass_snapshot), direct log reads (failures=1, the known #94 guard),
    and pixel statistics on fetched screenshots. The agent's verbatim
    diffs were never trusted (lesson 22) and nothing was needed from them
    that a raw probe couldn't prove harder.

36. **Stale dependency knowledge masquerades as an architecture mystery.**
    The niri half of the X-ray saga: xray blur is auto-enabled whenever any
    background effect is active, and it blurs the WALLPAPER ONLY (ignoring
    windows below) — those semantics sat in the 26.04 wiki the whole time
    while we reasoned from a pre-blur mental model ("niri has no blur" was
    my training belief). When a bug smells like a dependency's semantics,
    refresh capability knowledge from its source repo BEFORE theorizing
    (skills/SKILL-codebase-docs-updater.md → knowledge/niri.md). And warn
    the user proactively: non-xray blur is upstream-experimental (vanishes
    during open/close animations and tiled drags) — don't let it be
    mistaken for a regression in #96.

37. **Audit-filed issues are often already fixed — verify before
    planning.** Of 8 open issues in the triage session, 4+ were resolved
    in-tree by later commits but never closed (the audit bot committed
    fixes without closing its own issues). The efficient loop: read each
    issue's acceptance criteria → probe current main (grep the cited
    lines/files, run the named gates) → close with an evidence matrix,
    and only write new code for the genuinely-unfixed remainder.

38. **A test that exists is not a test that runs.**
    `tests/action_registry_async.py` holds the #66 regression suites but
    doesn't match unittest's `test*.py` discovery pattern; it only runs
    classes IMPORTED by `test_action_registry.py` — which imported just
    one. Both "existing" regression suites were dead code in G0 (a
    size-ratchet comment even explained the import trick). Check WHERE a
    test class executes (grep the discovery module), not merely that the
    file exists — and beware `@skipUnless` env gates hiding pure
    source-string tests that need no such gate (#94's drift survived
    exactly there).

39. **Idle-CPU attribution without perf: deltas + SIGSTOP A/B + poor
    man's gdb sampling.** No perf/strace on the box → /proc task utime
    deltas (per-thread table), 120× gdb `thread apply all bt` samples
    (all threads in ppoll/futex ~97% ⇒ cost = wakeup frequency), and a
    controlled SIGSTOP of the backend for 60 s (CPU unchanged ⇒ backend
    exonerated; the 84 KB/2 s JSON pipeline costs ~nothing). The real
    driver: an always-on full-screen layer animating at every vsync
    (`MediaAmbient { playing: true }` in DesktopAmbient). Fix =
    frameTime-accumulation budget (~22 ms) in the FrameAnimation —
    refresh-rate independent, motion speed preserved, measured 10.0% →
    5.75% of one core. Note: FrameAnimation has no `timestamp` property
    on this Qt — use `frameTime` accumulation; and VLM screenshot checks
    misname the compositor (niri → "Hyprland") while still verifying
    panel content correctly.

40. **Perceived latency ≠ CPU: measure dim→arrival with wf-recorder.**
    The PR46-vs-main A/B (2026-11-08) showed main better on every CPU
    metric, yet the user called it laggy. The perceptible culprit was
    the cold-open dead window: scrim dims → 300-450 ms of nothing →
    whoosh. Recipe that measures what the user SEES: wf-recorder 60 fps
    of an IPC-driven toggle, then per-frame region stats (mean R for
    scrim tint, FIND_EDGES variance for blur/sharpness) — dim-start to
    panel-arrival is the number that maps to "khựng". Partial feedback
    followed by a stall reads laggier than one clean freeze; latency
    budgets must be spent on feedback→content, not feedback→wait.

41. **`lme-shell.log` growth is a liar (stdio block-buffering).** With
    start.sh's `exec >> log 2>&1`, quickshell's stderr is block-buffered:
    the file can sit byte-frozen while the shell renders 90 KB/s of
    QSG_RENDER_TIMING lines into an 8 KB buffer. Never conclude "zero
    frames" from a frozen log — either pump the volume until it flushes
    or redirect to a file you control (`start.sh` with your own
    `> /tmp/qs_start.log 2>&1` wrapper) before trusting log-based frame
    analysis. Screenshot-pair diffs settle "is it rendering" in 10 s.

42. **Verify the documented limitation before blaming it.** The niri
    snapshot says non-xray blur "disappears during window open/close
    animations" — tempting theory for the glass flicker feel, but
    wf-recorder frame analysis proved the blur STAYS active during
    lme-shell's layer-surface flights (edgeVar low whenever tint
    present). The limitation covers niri's own window animations, not
    client-driven layer movement. Same for the ambient-judder theory:
    the drift is 5-27 px/s = sub-pixel per 24 ms update, invisible at
    41 fps. Both plausible theories died on arithmetic/evidence in
    minutes — always run the number before shipping the explanation.

43. **A ratchet gate nobody re-runs goes stale silently.** Main was RED
    on `check_architecture.py` size caps (ShellState.qml 261, shell.qml
    255 > 250) since #104/#105 grew the files without ratcheting —
    discovered only when a new PR ran the battery. And mind the shell
    you run it from: `./scripts/check.sh | tail -40` returns TAIL's
    exit code — capture `CHECK_EXIT=$?` into the log, not the pipe.

44. **Prewarm pattern for retained-panel architectures.** One-shot
    timer N seconds after startup: `dormant = true` BEFORE
    `mounted = true` (keeps surfaceLive false → no scrim/blur/viewport
    side effects while the async incubation builds), then
    `onLoaded → finishClose()` parks it like any dormant tree. First
    Control Center open after login: 460 → 33 ms, no visible prewarm,
    +132 MB RSS at t=4 s (the same steady state keepAlive converges to
    at first open anyway). Watch the Loader semantics: assigning the
    SAME Component to sourceComponent is a no-op (no reload), so a
    prewarmed tree survives the later real open unchanged.

45. **Repeater.itemAt() is not notifiable — pair it with a population
    revision.** Under async incubation (Loader `asynchronous: true`,
    including the #107 prewarm), `count` reaches its final value BEFORE the
    delegates are instantiated (itemAdded observed firing in REVERSE order,
    5→0). Any binding like `count ? itemAt(i) : null` latches null and never
    re-runs — neither count nor the index changes when the delegate finally
    exists. Symptom class: "indicator/accent missing on first open until
    the user switches tabs". Fix pattern (PR #108): `property int
    population` bumped in onItemAdded/onItemRemoved, referenced as a
    statement inside the binding body to create the dependency. Related
    trap: verify WHICH component your IPC path instantiates before calling a
    probe "not firing" — `toggle settings` in non-demo starts the standalone
    settingsProcess, not the in-shell SettingsPanel (both use SettingsView).

46. **Invisible GPU warm-up: layer + opacity 0, viewport-only expansion.**
    A parked dormant tree has never rendered, so the first open pays glyph
    raster + atlas/texture uploads mid-flight. A once-per-session warm pass
    (reserve the open frame in the viewport ONLY — surfaceLive/scrim/blur/
    mask/focus stay false — tree at open geometry inside `layer.enabled`
    with opacity 0, ≥3 forced frames, then exact park restore) is invisible
    (wf-recorder region diffs flat) and free (RSS +0.9 MB noise). Measured
    (PR #109): glyph 10→6, atlas 398→238, flight arrival 467→417 ms,
    discontinuities 6→3. Honest limits: PARTIAL — a pure `opacity: 0`
    without the layer does NOTHING; even with the layer it does not equal a
    real on-screen render (does not reach reopen-class, render>4ms frames
    remain). Set expectations accordingly and say so in the PR body.

47. **A size morph must follow the flight, not the mount state.** The island
    ESC-race ("open + ESC looks stuck then closes") was not a rendering or
    timing bug: in spring mode the width/height spring targets keyed on
    `mounted && !dormant`, so a mid-expansion close reversed the flight
    springs while the island kept GROWING as it left. Non-spring mode keyed
    the size on progress and never showed it. Whenever two spring families
    animate one surface, key them on the same driver (shown/flight state),
    not on lifecycle flags that flip at park time.

48. **Extending a warm-up pass to a size-morphing surface needs three extra
    pieces.** The CC (#109) has fixed geometry; the island morphs. (a)
    `visible` must include warmupActive — a visible:false item renders
    nothing into its layer; (b) size springs must SNAP to open geometry for
    the forced frames (they'd still be mid-expansion otherwise, warming only
    the visible slice) and snap back to the park size after, so the next
    real open still animates from compact; (c) surfaceLive must EXCLUDE the
    warm pass even though `visible` now includes it, or the scrim window
    maps and the blur region activates during the "invisible" render.

49. **Gated test suites rot silently behind their env gates.** Three suites
    (popup-motion, popup-entry, release-session/render-lifetime via the
    shared fixture) still waited for panels to UNMOUNT after close — stale
    the moment #105 introduced keepAlive retention (surfaces park DORMANT,
    mounted stays true). Nothing failed because LME_TEST_MOTION_UI /
    RELEASE_SESSION / RENDER_LIFETIME gates skip by default; the next gated
    desktop run would have gone red for unrelated reasons. When a PR changes
    a lifecycle semantic (unmount→park), grep the gated suites for the old
    assertion the same day, and prefer liveness (`mounted && !dormant`) over
    mount booleans in fixture state contracts.

50. **The repo's size ratchet counts comments as nonblank lines.** A
    documentation pass looks "free" but every comment line burns headroom
    against `config/architecture.json::largeFiles` ceilings (default 250).
    Compute headroom per file FIRST; headroom-0 files (desktop_backend.py,
    shell.qml, ShellState.qml, Theme.qml...) accept only trailing same-line
    comments, and the architecture check must run after every batch.

51. **A docstring inserted above SPDX/old docstring is a real AST break**
    (stray string expression + `__doc__` hijack), caught only by
    ast.dump-with-docstrings-stripped comparison — qmllint/tests would not
    notice. Extend the original docstring; never insert before it.

52. **Prove flakes environmental with a baseline worktree, not isolation
    passes.** SettingsStartup's reconnect test failed full-suite on HEAD but
    passed isolated — inconclusive. `git worktree add /tmp/base <baseline>`
    + full-suite run THERE failed the same way → diff exonerated with
    verbatim evidence on both sides.

53. **The OpenCode gateway's `idle` message goes stale after a new prompt.**
    A waiter that returns on "last idle seen" exits instantly with the
    PREVIOUS run's report. Count only idles appearing after the last USER
    message (tools/wait2.py in this archive).

54. **Agents told to be "proportionate" under-deliver coverage** (skip every
    file that already has a docstring) and will reference ephemeral /tmp
    note paths inside docstrings. Countermeasures that worked: explicit
    per-file coverage audit with a log ("missed 0" required), and a
    `rg '/tmp'` sweep before the docs commit.

55. **Comment-only diffs are provable, cheaply.** Python: ast.dump minus
    docstrings, byte-compare vs baseline (276/276). QML/JS/GLSL/sh:
    string-aware comment stripper (reuse check_architecture's TOKENS regex)
    + whitespace normalization (167/167). This battery caught 3 real breaks
    the agent had introduced while "only adding comments" — run it; do not
    eyeball 445 files.

56. **Audit annotation "hallucinations" with a tolerant grammar parser, not
    the spec grammar.** Real REL tags drift from the spec (`pathA, pathB –
    reason`, `::sym1,::sym2`, `(.qsb)` suffixes, bare filenames inheriting a
    sibling's directory, root-level files like THIRD_PARTY.md). A strict
    parser reports false "parse errors"; a tolerant one resolves every
    reference (repo-root → tagging-file dir → comma-list dir inheritance →
    unique basename) and only then judges. The hallucinations that remain
    are semantic: invented symbol names, right relationship pinned to the
    WRONG file, action attributed to the wrong provider — catch those by
    grepping the claimed symbol/action inside the claimed file, not by
    checking path existence (paths were 180/180 real while 5 claims were
    still wrong).

57. **Verify map file:line anchors by CONTENT at the line, in the state the
    map claims to describe.** "Path exists + line in range" passes for
    stale anchors. The 2026-11-09 map pinned check_architecture.py refs to
    the BASELINE (pre-annotation) line numbers even though the annotation
    pass itself had shifted that file +6 lines — internally inconsistent
    with every other anchor. Rule: after a self-modifying pass (comments
    shift lines), re-pin ALL map anchors against the final tree, or state
    explicitly which tree the numbers refer to.

58. **Quick tunnels + agent bridges: submit-then-poll, never background-
    poll.** A local `python3 bridge.py ask ... &` poller dies with the
    sandbox shell (tool calls don't keep processes alive), losing the
    job_id when the tunnel later drops. Submit async, print+persist the
    job_id IMMEDIATELY, then poll in short foreground calls — when the
    tunnel dies (HTTP 530 → DNS gone) the server-side job may survive and
    be retrievable by job_id once a new URL arrives. For payload transfer
    through chat: xz -9 | base64 -w76, ~30-48KB chunks between explicit
    markers, whitespace-stripped reassembly + md5 of the DECODED artifact
    (chunk-level md5 can differ on trailing-newline position while content
    is still byte-identical).

59. **Dual-model audits catch different defect classes — run both when the
    stakes justify it.** The 2026-11-09 annotation audit: GLM caught the
    wrong-provider attribution (`powerProfile` in audio_actions vs
    desktop_backend) that Beam missed; Beam caught the misnamed function
    (`::planning` vs `plan`) that GLM's word-level grep accepted. Two
    independent routes converged on 103/108 identical PASSes and the same
    2 hard FAILs — the value of the second route was exactly the 2 items
    they disagreed on, both resolved by arbitration against the real repo.
    Single-auditor confidence is a ceiling; disagreement is a signal, not
    noise.

60. **OpenCode gateway model routing: read /api/model for providerID, and
    "Max" is a VARIANT not a model id.** `beam` (Beam 1.0 501B A23B) is
    served by provider `ollama-cloud`, not the default `opencode` provider;
    POSTing {"modelID":"beam"} or provider `opencode` fails with a SILENT
    provider.no-route (session outcome "failed", error only visible in the
    context idle entry). Correct body: {"model":{"id":"beam","providerID":
    "ollama-cloud","variant":"max"}}. Always verify the model actually used
    via the assistant message's `model` field — the first run silently
    executed on iceman-free and produced a valid-looking report.

61. **Bulk payload transfer through an LLM-proxy bridge corrupts; a direct
    shell endpoint does not.** Sending a 20KB base64 patch inside a chat
    message to the Command Code worker made the worker LLM re-type the
    heredoc — md5 mismatch (silently corrupted; the md5 gate caught it,
    tree stayed clean). Same machine, OpenCode gateway POST
    /api/session/{id}/shell {"command": ...} executes DIRECTLY (no LLM),
    output readable from the resulting shell message (type=shell,
    status=exited, output.output) — the printf-base64 pipe arrived md5-
    identical. Rule: pass artifacts through the direct-execution path and
    md5-gate BOTH ends; never ask an LLM to re-type kilobyte payloads.

61. **Refresh the dependency snapshot BEFORE designing a plan against it —
    the plan's value is the grounding, not the prose.** The QML-first
    migration plan (lme PR #113) hinged on "what can Quickshell 0.3.2 do
    natively"; training memory said "no Bluetooth API, no NetworkManager
    bindings" — both WRONG (0.2.0 added full BlueZ incl. per-device battery
    and pair/connect/forget; 0.3.0 added NM bindings incl. connectWithPsk
    and NMSettings.read/write). A plan written from memory would have kept
    nmcli/bluetoothctl wrapping in Python forever. One shallow clone +
    `rpm -q` on the user's machine + Q_PROPERTY greps over the headers
    redesigned the whole phase structure in ~20 minutes. Snapshot now
    lives at knowledge/quickshell.md; keep it stamped with the version
    floor (0.3.2) and re-verify before each new design cycle.

62. **Quickshell 0.3.2 normalizes UPower `percentage` to a 0–1 fraction —
    and units are a contract, not a detail.** Q1 (lme PR #115) rescaled
    Pipewire volume, wifi signalStrength and Bluetooth battery by 100 but
    read `UPowerDevice.percentage` as 0–100, so an 80% battery rendered as
    `Math.round(0.8)` = 1% — owner-visible regression, invisible to every
    sandbox test because the native path only engages in real sessions.
    Two structural fixes: (a) the A/B drift log DID catch it same-day
    (`backend 79 vs native 1`, 27/27 lines) — keep A/B windows on every
    native port and actually READ them on the real machine; (b) grep the
    dependency source for `DBusDataTransform`/unit transforms at every
    service boundary BEFORE writing the QML side, not after the bug
    report. knowledge/quickshell.md row 5 now carries the gotcha; fixed
    in PR #116 (percent100() helper + source-contract + behavioral tests).
63. **Owner model preference for remote audits (2026-11-09): use
    `crouton-alpha-free` (provider `opencode`, variants up to `max`,
    free) — NOT `iceman-free`** — when driving the OpenCode gateway agent
    on the real machine ("ưu tiên models tốt như crouton alpha ... thay
    vì iceman free"). Same switching mechanics as lesson 60: POST
    /api/session/{id}/model {"model":{"id":"crouton-alpha-free",
    "providerID":"opencode","variant":"high"}}; verify via the session's
    model field AND the assistant message `model` field (silent
    provider.no-route history). Used for the Q1 battery audit:
    ses_e3f9c7448ffeOmmA2GvCyVyPto, worked first try, high reasoning
    quality (correctly cross-checked D-Bus, log, backend, source).

64. **Target-engine API surface is a contract too (Q2, lme PR #117): the
    sandbox CANNOT catch V4-engine gaps.** Two blockers surfaced only on
    the owner's real machine (quickshell 0.3.2 fc44): (a) `native` is a
    RESERVED QML identifier — `readonly property bool native:` is a
    parse error that breaks the whole singleton import chain (ES3
    future-reserved words still rejected by V4 even though desktop JS
    engines allow them); (b) `Object.fromEntries` (ES2019) does not
    exist in V4 — runtime TypeError at load. Sandbox has no quickshell
    binary and Node/V8 have ES2019, so both passed locally. Mitigations
    now in the repo: `scripts/check_qml_reserved.py` (sandbox scanner,
    all 164 QML files) + a source-contract test banning `fromEntries`
    and reserved-word property names across `qml/services` (comments
    excluded — the scanner's own explanatory comment tripped the first
    version). ES2017 (`padStart`, `Object.values`) is proven fine on the
    live shell; assume ≤ES2017 + explicit greps for anything newer.

65. **Real-machine QML test/probe harness patterns (Q2 rounds 1–4):**
    (a) `finish()`/`Qt.quit()` must fire from a Timer, never from
    `Component.onCompleted` (no receiver → hangs to the 15 s timeout) —
    same lesson as eb5f2db, re-learned in a new test; (b) readiness-poll
    async sources instead of fixed waits: DesktopEntries scan, FileView
    loads and backend snapshots all took >1.2 s on the real machine
    (deadline 8 s inside run_qml's 15 s timeout; the Q1 `backendReady`
    phase-gate pattern is the reference); (c) standalone probes must
    live INSIDE the worktree with a RELATIVE import
    (`import "qml/services"`) — absolute paths are "not a valid import
    URL" in 0.3.2; (d) probe `console.log` needs
    `QT_LOGGING_RULES=qml.debug=true` or it is suppressed; capture
    stdout+stderr combined; (e) a probe that sets XDG_DATA_HOME for
    isolation hides user-local ~/.local/share/applications entries —
    11-app "backend-only" diff was an artifact, compare against the
    un-isolated backend view or unset it; (f) cleanup order matters when
    the probe is inside the worktree: rm the probe BEFORE
    `git worktree remove` (untracked files make it refuse).

66. **First write-family port (Q3, lme PR #118): settle pending locally, never
    fake a backend round-trip.** The router reserves the action's pending slot
    with Pending.sent, executes natively, and settles with a NEW
    ActionPending.settled primitive — because received() only un-pends actions
    the backend acknowledges, a locally-served action would hang pending
    forever. Results surface through the same lastResult/wifiResult/status
    path so widget UX (awaitingConnection, busy flags, dialog close) is
    unchanged. Fallback ordering matters: fixture modes keep the demo
    registry; real sessions without quickshell's NetworkManager backend or
    adapter fall back for the backend's canonical error strings. Probe lesson
    (round 1): dispatching a native action at t=0 falls back — the devices
    model loads async, so canRoute() is false until it lands; probe AFTER
    canRoute() && section.device, and give RequestScan its full ~10 s
    rate-limit window before comparing lists.
67. **quickshell 0.3.2 wifi write API — verified semantics (Q3 source
    reading + real-machine parity):** WifiDevice.networks is SSID-deduped
    (matches nmcli first-seen dedupe); Network.nmSettings attaches saved
    profiles per-SSID, so the saved list = union of network.nmSettings
    (hotspot ap-mode profiles are SKIPPED — quickshell TODO); connect() on a
    network with settings activates that profile, with an AP add-and-activates
    otherwise; connectWithPsk on a saved network UPDATES the profile's psk
    then activates (no duplicate profiles), on a new SSID add-and-activates;
    Network.forget() drops EVERY profile on the SSID — forget one uuid via
    NMSettings.forget() on the specific object; scannerEnabled false->true
    re-arms RequestScan (rate-limited 10001 ms; a retry timer fires later);
    WifiSecurityType enum maps to display strings (Wpa2Eap = enterprise);
    ConnectionFailReason drives the auth-failure UX. Backend parity achieved:
    identical SSID sets and 0 strength deltas vs nmcli on the owner's machine.

68. **Remote audits review semantics, not JS arity — self-review every
    callback call site (Q3 part 2, lme PR #119).** The crouton audit round
    PASSed `finish(evaluate())` where finish(ok, message) expected two args —
    the [ok, message] array bound to `ok`, message undefined; only a
    line-by-line call-signature re-read after pushing caught it (fix 72af7ce,
    verified round 2). Rule: after writing any done/callback flow, re-read
    every call site checking arity + types against the signature, and prefer
    test pins over prose audits for shape bugs. Same round taught three more
    ports rules: Python round() is ties-to-even while JS Math.round is
    half-up — port numeric helpers with tie-case tests (50.5→50, -99.5→-100);
    quickshell Process FailedToStart emits runningChanged but NEVER exited,
    so one-shot tools need an armed+exit-seen guard plus a watchdog that is
    stopped in the settle path (else it kills the next queued run); and
    native writes to PwNodeAudioIface.volume are the same scale wpctl prints
    (write 80% read back 0.80 in wpctl, A/B drift stayed 0) — the Q1 read
    parity argument extends to the write path.

69. **OpenCode gateway API shapes (Q4 rounds, 2026-11-10):** model switching
    is `POST /api/session/{sid}/model` with `{"model":{"id":"...",
    "providerID":"..."}}` — a Model.Ref OBJECT, not a string (a string 400s
    with "Expected Model.Ref"). The owner's preferred model is
    `opencode/deepseek-v4.1-flash`; it can 402 "Insufficient balance" — the
    fallback that worked is the same model's free variant
    `opencode/deepseek-v4.1-flash-free` (same family, same tool quality).
    Session IDs from `GET /api/session` must be copied FULL-LENGTH (a
    truncated id returns SessionNotFoundError). The message list endpoint
    returns `data` as a plain array (older builds wrapped `{messages:[...]}`)
    — parse both. Keep the active session id in a local env file (e.g.
    `~/.oc-env`, chmod 600) and ALWAYS verify which session a prompt went to
    before waiting on it — a stale id silently sends the task to the wrong
    session (interrupt it immediately: `POST .../interrupt` returns
    `{"interrupted":true}`). Reusing one long-lived verify session across
    rounds is efficient: the agent remembers its worktree/venv/pointer
    setup; just `reset --hard` the worktree each round.

70. **Q4 engine-first-run socket lessons (lme PR #124/#125):** three bugs
    the sandbox rounds could not see, all caught only when the engine cases
    first ran on quickshell 0.3.2: (a) reusing ONE `Socket` across requests
    loses writes — flipping `connected` false→true while the previous
    connection still tears down never re-emits `connectedChanged`, the
    queued line is never written and the abandoned teardown SIGSEGVs the
    engine; build one fresh Socket per request (inline Component +
    createObject + deferred destroy(1000) + per-socket settled guards).
    (b) The niri IPC protocol NEVER speaks first — a long-lived stream
    socket must WRITE the subscribe line (`"EventStream"\n`, quoted JSON
    string) from inside `connectedChanged(true)`; setting `connected=true`
    alone opens a silent socket and the section silently degrades to the
    polled reads. (c) A contract test that asserts a string like
    `"EventStream"` in the source matches COMMENTS too — the bug hid behind
    the REL header's prose for two sandbox rounds. Pin the real call
    (`assertIn("write('\"EventStream\"\\n')", code)`) so prose cannot
    satisfy the contract. Rule: every ported protocol write needs an engine
    case that observes the wire (the fake-socket fixture pattern), and every
    source-string contract must assert the call shape, not the token.

71. **Q4 legs 2-3 engine-first-run lessons (lme PRs #126/#127):** the families that
    own LONG-LIVED daemons (wl-mirror/wlsunset/swayidle) hit a new defect class:
    (a) A snapshot-hook call MUST match the service's signature — the hook called
    `MirrorState.recheck(preferences)` while recheck took `(done)`, so accept()
    threw a TypeError on EVERY real-session snapshot, silently skipping backendReady,
    toasts, catalog validation and stayAwake (only the real-session engine fixture
    caught it; contract tests pin the call shape now). (b) Section `running` must
    track the SPAWNED COMMAND (cleared synchronously in close()), not the QProcess
    property (which only flips on the actual exit) — the backend's child-is-None is
    synchronous; same for stopMirror's command clear, else restart-after-stop says
    "busy". (c) A start IN FLIGHT must count as busy (`starting` flag) because the
    native router runs dispatches concurrently where the backend's request loop
    serialized them. (d) quickshell 0.3.2's real `niri msg` CLI sends a Version
    handshake after Outputs reads — a fake unix socket cannot serve it (protocol
    hash check); use a PATH-injected fake niri SCRIPT for engine cases instead,
    and keep live-socket parity as a real-machine probe. (e) A PATH block CANNOT
    hide an installed binary — shutil.which and execvp CONTINUE past a directory
    or non-executable entry (verified: which('wlsunset') still found /usr/bin one);
    missing-tool engine cases must skipIf(shutil.which(tool)). (f) Engine fixtures
    that override environment from os.environ under the migration gates inherit
    QT_QPA_PLATFORM=wayland — pin offscreen/software explicitly when the case also
    overrides XDG_RUNTIME_DIR (the gate's Sway socket lives there). (g) Engine
    tests must NOT subclass LocalQmlCase (double collection — borrow
    `run_qml = qml_tests.LocalQmlCase.run_qml` on a unittest.TestCase instead),
    must insert scripts/ on sys.path themselves, and spawn-marker tests need a
    settle phase (~3 s) before stopping — the PDEATHSIG helper's exec is not
    instant. The verification cadence that worked: suite → regression case → full
    suite → live parity probe → crash-dir counts → gates, re-run per hotfix.

## Lesson 72 — Minewrap Phase A (2026-11-11, session 2)

1. **Sandbox /tmp is wiped between sessions** — anything live there (`.oc-env`
   gateway credentials, `/tmp/.ghtoken`) is gone even when `/home/z/my-project`
   survives. Persistent secrets must be re-requested from the user at session
   start; git remotes with embedded PATs DO survive (in `.git/config`).
2. **Minewrap config path semantics bit twice**: (a) TOML relative paths
   resolve against the CONFIG FILE's dir (`resolve_paths`, config.rs) — not
   the daemon cwd; (b) `java_path` resolves against the SPAWNED SERVER's cwd
   (= work_dir) — a stub `./fakejava` must be symlinked into each work_dir.
   Harness encodes both rules (`resolve_cfg_path` + `ensure_stub_links`).
3. **Never trust tool-side partial failures**: the Edit/MultiEdit tools can
   report "no replacement performed" while earlier edits in the batch still
   landed (non-atomic in practice). After any reported edit failure, re-read
   the file and diff intent vs content before re-applying.
4. **rg display mangles `[min…]` bracket sequences** in some outputs — verify
   disputed file bytes with `od -c`/python before "fixing" a non-bug.
5. Waiting on a daemon's REST state field only works if something updates it:
   v1.9.3 minewrapd `combined_state` is dead-stale (GapB) — the harness waits
   on `/logs` (Done line + growing last_seq) instead, and RECORDS the stale
   state as runtime evidence.
6. **New defect class confirmed (GapF)**: state machines with `assert!` on
   allowed transitions panic on error paths (spawn_failed from Offline) —
   error paths need explicit transition handling, and memtest harnesses that
   intentionally trigger spawn failures are good fuzzers for this.
7. User-mandated clean-repo policy (Q8) is a standing constraint: app repo =
   docs + app code + build script only; measurement tooling lives outside
   (user machine `~/dev-memtest/` + archive repo `tools/memtest/`).

## Lesson 73 — Minewrap Phase A completion (2026-11-11, session 2 cont.)

1. **Terminal display layer can EAT the substring "[mi"** from tool outputs
   (seen with both rg and remote-shell cat): "median [min–max]" rendered as
   "median in–max]" — which triggered a false "typo still broken" spiral.
   Rule: before "fixing" mangled text seen through ANY display layer, dump
   the bytes (`od -c`) or read via python. The file was correct all along.
2. **`str.replace` fix verification must not use a substring of the
   replacement**: '[min–max]' CONTAINS 'in–max]', so `"in–max]" not in s`
   reports False even after a successful fix — verify with an unambiguous
   marker ('[min' with the bracket) instead.
3. **opencode paid model 402 (Insufficient balance) is the default failure
   now** — `deepseek-v4.1-flash` paid is out of credits; the `-free`
   variant of the same family handled the full A2 run (clone + build +
   14-scenario measurement + honest STOP-gate report) without issues.
4. **oc_prompt.py truncates its JSON echo at 400 chars** — piping that
   through `json.load` fails on the truncation point; treat its output as
   fire-and-forget and verify via `GET /message` instead.
5. **One-off memory step-downs during idle sampling are real system
   events** (S0#1 dropped 5.85→4.10 MiB RSS at t=24 s, never reproduced in
   3 later runs): don't chase them as harness bugs — reproduce first;
   median-of-runs absorbs them; note them in the report.
6. **Agent-vs-GLM cross-verification protocol works**: re-measuring 3
   scenarios directly via raw-shell agreed with the agent's numbers within
   0.01–0.20 MiB — that's the evidence bar for trusting the rest.
7. Baseline drift is expected between measurement campaigns on a desktop
   machine (WebKitGTK version bump moved GUI PSS +13.72 while RSS moved
   +2.43): always re-baseline with the SAME harness before optimizing, and
   compare KPIs against the fresh numbers, not the historical report.

## #74 — Minewrap Phase B/C session (2026-11-11, session 3)

1. **Dead code hides broken code**: the v1.9.3 SLP client
   (`request_status`) had wrong read-offset math — its happy path had
   NEVER run (poller had zero callers, gap G3). When reviving dead
   features, assume the happy path is broken until a live test proves
   otherwise; the fake-SLP-server unit test found it in seconds.
2. **`#[tokio::test]` runs a current-thread runtime**: `std::thread::sleep`
   inside such tests freezes every other task (state keeper never folds
   events → probes skip → `server.await` hangs forever). Always
   `tokio::time::sleep().await` in async tests, even for "just let the
   background task catch up" waits.
3. **tungstenite 0.24 `connect_async` requires the caller to supply the
   full handshake header set** (Host/Connection/Upgrade/Version/Key) when
   passing a prebuilt `http::Request` — a bare URI request fails with
   `InvalidHeader("sec-websocket-key")`. `handshake::client::generate_key()`
   is public; build the headers explicitly (see minewrap-remote
   `ws_request`). This also means the v1.9.3 `events_connect` (string URL,
   no headers) could never have authenticated even with a caller.
4. **Sandbox without GTK can still verify GUI-adjacent code**: a scratch
   crate that `#[path]`-includes the tauri-free `node_service.rs`
   (`scripts/gui-check/`) type-checks + integration-tests the registry
   round-trip. Cheap insurance before shipping the real build to the
   remote machine.
5. **`tools/oc.sh` breaks with a user:pass `OC_AUTH` env** (passes it as a
   header via `-H`); `rsh.sh` works because it uses `curl -u`. When the env
   file holds `opencode:<pass>`, use `curl -u` helpers (`scripts/oc-fire.sh`
   / `oc-report.sh`), not `oc.sh`.
6. **Python-scripted brace surgery on Rust files is fragile** — inserting
   methods "before the last `}`" landed them after a trailing free
   function (double `}` at EOF). Fix pattern: locate the free fn marker,
   split there, never trust `rfind` on the whole file. Better: use the
   Edit tool with exact anchors.

## #75 — Minewrap session 4: verify-everything round (gate 2/3 evidence)

1. **rsh.sh auth forms**: `tools/oc.sh` uses the Basic header form, `rsh.sh`
   uses `curl -u` — keep `OC_AUTH` as RAW `user:pass` and a separate
   `OC_BASIC` (base64) export; mixing them silently turns every poll into a
   401 loop that looks like a "gateway hang" (240 s of sleep-2s polling).
2. **Sandbox background jobs get reaped**: `nohup cmd &` from a Bash tool
   call died twice mid-download; `setsid nohup ... < /dev/null & disown`
   survived. Foreground `timeout 560 cargo fetch` then `cargo test` is the
   reliable pattern on the 2-core sandbox (deps for 3 headless crates fit
   in one 10-min window after a fetch pass).
3. **Demo scripts: header bugs hide as app bugs** — `-H "$TOK"` instead of
   `-H "Authorization: Bearer $TOK"` produced 401s that looked like "start
   not working / server died". Evidence-first debugging caught it in the
   log ({"detail":"invalid or missing bearer token"}); re-ran with fixed
   headers before drawing conclusions. Always print the raw error body in
   acceptance scripts.
4. **Timed-exit checks are racy with pgrep**: "daemon still alive after
   SIGTERM" was twice a false alarm (pgrep matched an older unrelated
   daemon / a dying process). Measure with `kill -0 $PID` on the exact pid
   and a monotonic clock, and print the elapsed seconds — real number was
   0.0 s idle.
5. **UI assets are not built by `cargo build`**: a Tauri GUI built via bare
   `cargo build -p minewrap-tauri` without `pnpm build` (ui/dist) compiles
   fine but ships an empty frontend — build via the repo's `build.sh` or
   stage `pnpm build` first, else K2/GUI measurements measure a blank page.
6. **Same-day re-baselining matters**: PSS shared-page accounting drifted
   +13.7 MiB on the GUI between the v1.9.3 report and today's re-measure
   (WebKitGTK 2.54.2 upgrade) — always compare against same-day baselines
   when the KPI is a delta.

## #76 — Minewrap session 5: P1 kickoff + vision pipeline (2026-11-11)

1. **Process-level "GUI works" proves nothing about pixels.** The P0 GUI
   binary on the machine showed a WebKit error page ("Could not connect to
   localhost: Connection refused") while EVERY process-level check was green
   (pgrep alive, auto-spawn log, REST state, server-survives). Session 4's
   "GUI opens" evidence was all process-level. Bar for GUI verification:
   focus the real window, screenshot it, and look at it (VLM) — anything
   less is unverified.
2. **niri full-screen shots hide off-viewport windows** (scrollable tiling):
   plain `grim` "verified" nothing because the window sat outside the
   viewport. Sequence that works: `niri msg --json windows` (NOTE: returns a
   BARE ARRAY, not {"windows": [...]}) → `niri msg action focus-window --id
   N` → `grim` → refocus the user's previous window (be a polite guest).
   NIRI_SOCKET may need to be derived from `$XDG_RUNTIME_DIR/niri*.sock`.
3. **Tauri release binary + empty ui/dist = "Could not connect to
   localhost"**: frontend embedding happens at compile time
   (generate_context!, frontendDist ../ui/dist); bare `cargo build
   --release` without a prior `pnpm build` silently ships an error page.
   Always build the frontend first, or use the tauri CLI.
4. **build.sh was shipped untested** (B9): its GUI path references
   ui/src-tauri (doesn't exist) and `pnpm tauri` (no such script). Every
   script that is itself a deliverable must be executed end-to-end at least
   once, in every mode it advertises.
5. **Gateway bg-launcher + `~` paths don't mix**: oc.py bg's redirect fails
   on `~/...` logfiles — use absolute paths in both command and logfile.
6. **pkill -f self-match**: `pkill -f fakejava` killed the gateway shell
   running it (its own cmdline matched the pattern). Use the bracket trick
   (`pkill -f "fake[j]ava"`) or exact-name `pkill -x`.
