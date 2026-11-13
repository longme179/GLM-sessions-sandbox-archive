# Q5 ACTIVE STATE — read this FIRST on any new session

Last updated: 2026-11-13 (session 3: Q5 leg 1 CODED + PR #130; OpenCode credential rotated → remote verification PENDING)
Owner approved Q5 on 2026-11-12: "duyệt Q5 (weather, lyrics, wallpaper, file search, equalizer,
clipboard — fileOpen cũng chuyển theo entry search của Q5)". Standing rules: sub-agent prompts
in English, opencode > openrouter, deepseek-v4.1-flash-free > nemotron-3-ultra-free, remote
files under ~/glm-work/ only, owner merges PRs (never self-merge).

## CURRENT BLOCKER — OpenCode 401

Both stored credentials (/home/z/my-project/.oc-auth and .oc-auth.b64) are REJECTED (401
Unauthorized) by the gateway in scripts/oc.sh (tunnel alive, password rotated). Per the skill
policy: 401 → stop, never work around. **The owner must update the credential** (send the new
Basic-auth header value in chat, or restore access). Until then: NO remote work (engine tests,
live checks, sub-agents). Restore /tmp/oc_auth from the updated credential, then verify.

## Status

- [x] Blur bugfix PR #129 OPEN (awaiting owner merge) — engine green + probe-verified (session 2).
- [x] Q5 leg 1 (weather + lyrics) CODED: PR #130
      https://github.com/longme179/lme-fedora-niri-qs/pull/130
      (branch qml/q5-weather-lyrics, 3 commits: test → impl → docs).
      Sandbox G0 = clean-main profile (1222 collected, 0 failures, 3 quickshell-absent errors).
      PENDING (blocked by 401): engine cases tests/test_native_weather_lyrics.py on the real
      machine, qmllint there, live weather/lyrics checks. VERIFY BEFORE/AFTER MERGE.
- [ ] Q5 leg 2: wallpaper family (wallpaper.py / wallpaper_actions.py / wallpaper_palette.py /
      gowall_actions.py / palette_actions.py — 486 lines). Design first like leg 1.
- [ ] Q5 leg 3: file_search + file_search_actions (72) + fileOpen + equalizer_actions + audio_visualizer (494).
- [ ] Q5 leg 4: clipboard (315) — review-stop: propose Process.startDetached+PDEATHSIG vs
      stays-Python until Quickshell fixes destroy semantics; owner picks.
- [ ] Q5 close-out + archive records.

## Leg-1 implementation summary (for review / next session)

- WeatherState.qml + WeatherModel.js: XHR port of WeatherClient (same endpoints ipwho.is /
  open-meteo, same scheduling geo 3600/120 + forecast 900/120 + keep-last-good, same section
  shape/error strings), injectable loader/clock/wallClock for the engine cases. The Q4 owner
  registry routes weatherSearch/weatherDetect/weatherRefresh; weatherSelect STAYS BACKEND
  (writes preferences — Q6 boundary). NightLight follows WeatherState's resolved place.
- LyricsState.qml + LyricsModel.js: chain embedded → local LRC sidecar (FileView) → metadata
  check → disk cache → offline check → LRCLIB (XHR). Cache key = encodeURIComponent slug, TTL
  inside the JSON (storedAt — FileView has no mtime); old sha256 entries expire unread. Writes
  via the bounded `lyrics.py --store` helper (128-entry maintenance). LyricsSession's Process
  worker retired.
- Backend: --no-weather flag (real sessions spawn fetch-idle; Python sections stay the A/B
  window); DEPRECATED(Q5->Q6) markers on weather.py/weather_actions.py/lyrics.py.

## Session-3 gotchas (new lessons — add to lessons-learned at close-out)

- Sandbox recycled between sessions: /tmp wiped (oc_auth gone — normally restore from
  /home/z/my-project/.oc-auth; CURRENTLY STALE/401). Fresh sandbox ⇒ re-verify baselines.
- `ast.parse` does NOT catch repeated kwargs (`f(x=1, x=2)` parses, fails at import) — 107
  test modules died on one duplicate `weather_fetch=`. Use py_compile.compile(doraise=True).
- Size caps live in THREE places: config/architecture.json largeFiles + hardcoded numbers in
  tests (test_native_state SERVICES blanket 250; test_native_session + test_native_display_idle
  per-file SHELL_STATE/NATIVE_STATE). Bump all three together.
- git stash -u + ./scripts/check.sh = fast clean-main baseline (1192/0 fail/3 errors here).

## Remote verification checklist once access is restored (PR #130)

1. `cd ~/lme-fedora-niri-qs && git fetch -q && git worktree add ~/glm-work/q5leg1 qml/q5-weather-lyrics`
2. `cd ~/glm-work/q5leg1 && ~/glm-work/venv/bin/python -m pytest tests/test_native_weather_lyrics.py -v`
   (expect the WeatherState machine + lyrics chain green; the risk spot is FileView loaded/error
   semantics — readerSettled has a 400 ms fallback so missing files fall through).
3. qmllint the new/changed QML files; regression spot: tests/test_features.py + test_lyrics*.
4. Live (after owner merges + restarts): weather panel refresh/search/select; lyrics on a player.
