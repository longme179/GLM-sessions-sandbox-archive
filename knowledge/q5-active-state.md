# Q5 ACTIVE STATE — read this FIRST on any new session

Last updated: 2026-11-13 (session 4: legs 1+2+3a delivered and engine-verified; PRs #130/#131/#132 stacked, awaiting owner review)
Owner approved Q5 on 2026-11-12: "duyệt Q5 (weather, lyrics, wallpaper, file search, equalizer,
clipboard — fileOpen cũng chuyển theo entry search của Q5)". Standing rules: sub-agent prompts
in English, opencode > openrouter, deepseek-v4.1-flash-free > nemotron-3-ultra-free, remote
files under ~/glm-work/ only, owner merges PRs (never self-merge).

## Status — three stacked PRs awaiting owner review (merge in order)

- [x] **PR #130** leg 1 weather+lyrics (branch qml/q5-weather-lyrics, merged main after #129):
      engine 30 passed ×3, regression + qmllint green. MERGE FIRST.
- [x] **PR #131** leg 2 wallpaper scheduler (branch qml/q5-wallpaper, base = qml/q5-weather-lyrics):
      engine 20 passed ×2. After #130 merges, GitHub retargets to main automatically.
- [x] **PR #132** leg 3a file search + fileOpen + cava visualizer (branch qml/q5-search-visualizer,
      base = qml/q5-wallpaper): engine 18 passed ×2. Retarget after #131 merges.
- [ ] **Q5 leg 3b: equalizer** (equalizer_actions.py, 424 lines). EqualizerState.qml already has
      the full state machine (presets/staging/optimistic applies) — what stays backend is the
      serpantinum daemon runner (run with autostart retry — 'every push retries once after an
      auto-start') and the persisted eq_state document (storage.read_json/write_json — file
      writes need the lyrics --store helper pattern; eq_state.json read via FileView). Port:
      EqualizerState gains an injectable runner + a bounded `equalizer_store.py --store`-style
      helper (or extend an existing one); the 16 eq* actions route through the owner registry.
      DEPRECATED marker on equalizer_actions.py when done.
- [ ] **Q5 leg 4: clipboard (clipboard.py, 315 lines) — REVIEW-STOP**: propose
      Process.startDetached + PDEATHSIG (preExecCommand sets PR_SET_PDEATHSIG so the clip
      helper dies with the shell; quickshell 0.3.2 Process may kill children on destroy —
      the exact semantics need a probe) vs stays-Python until Quickshell fixes destroy
      semantics. Owner picks before coding.
- [ ] Q5 close-out + archive records.

## Session-4 deliverables (context for review)

- Leg 1: WeatherState/LyricsState (XHR ports, injectable loader/clock; lyrics cache slug +
  storedAt TTL; `lyrics.py --store`). Backend flags: --no-weather.
- Leg 2: WallpaperState/WallpaperModel (awww daemon ownership, plan() = pure due() port,
  setting-token writes via ShellState-injected closures; shared rotations delegate to the
  backend 'wallpaper' action). Backend flag: --no-wallpaper. Deviations documented in sources
  (no stat → apply-failure-driven; no symlink resolution).
- Leg 3a: FileSearchState (+ `file_search.py --worker`), fileOpen via gio with entry
  validation, VisualizerState direct cava (config/cava-visualizer.config shipped,
  audio_visualizer.py retired). No backend flag needed (request-driven actions).

## Engine-test lessons (add to lessons-learned at close-out)

- QML object literals in BINDING position need parentheses — `property var x: ({...})` —
  else the parser reads a block statement (quickshell exit 255).
- finish() must fire from a Timer tick, never from Component.onCompleted (quit before the
  receiver connects = 15 s timeout with all checks green).
- Python string replaces over test files: the files contain TWO backslashes (`\\n`) — search
  strings with one (`\n`) silently no-op. Always assert count == 1 before replacing.
- Unquoted object keys with hyphens (`{eDP-1: ...}`) are syntax errors — quote them.
- The awww/swww query format: `NAME: WxH, scale: 1, currently displaying: image: /path`
  (color rows carry no image; no parens).
- The step-helper pattern in tests normalizes prefs before each call — pass flags through
  the helper, never manual pref writes.
- Size caps live in THREE places (architecture.json + test_native_state blanket +
  test_native_session/test_native_display_idle per-file pins) — bump all together.
- Test frame corpora: count the values (17 semicolons = null frame = TypeError in the check).

## Remote access

oc.sh works again (credential from the 2026-11-13 handoff, stored in /home/z/my-project/.oc-auth
+ /tmp/oc_auth). Worktrees: ~/glm-work/q5leg1 (leg 1+merge), q5leg2, q5leg3. The venv:
~/glm-work/venv. Journal: /home/kimhoanglong/agent-collab/journal.md (append-only, Agent-2 entries).
