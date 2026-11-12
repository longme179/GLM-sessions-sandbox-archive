# Q5 ACTIVE STATE — read this FIRST on any new session

Last updated: 2026-11-13 (session 2: blur bugfix PR #129 + Q5 leg 1 design complete, coding not started)
Owner approved Q5 on 2026-11-12: "duyệt Q5 (weather, lyrics, wallpaper, file search, equalizer,
clipboard — fileOpen cũng chuyển theo entry search của Q5)". Also authorized: the Materials
popup-blur bugfix (delivered, PR #129).

## If you are a new session resuming this work

1. `cd /home/z/my-project/repos/lme-fedora-niri-qs && git fetch origin -q && git log --oneline origin/main -6`
2. Read `docs/QML_FIRST_MIGRATION_PLAN.md` §5 Q5, `docs/STATE.md`, `docs/MIGRATION_LOG.md` heads.
3. Read `/home/z/my-project/repos/GLM-sessions-sandbox-archive/knowledge/lme-shell-state.md` tail
   + `lessons-learned.md` (69-74) + this file. Continue the first unfinished item below.
4. Repo rules: tests→impl→docs commits, PINNED exact strings, REL/INVARIANT/GOTCHA comments,
   ratchets up only (line-sed config/architecture.json), .pragma library JS, pragma Singleton,
   DEPRECATED(Q5->Q6) markers, owner merges PRs (never self-merge).

## Status

- [x] Q4 closed (PR #128 merged, origin/main 47c91d0).
- [x] Blur bugfix PR #129 OPEN, awaiting owner merge: https://github.com/longme179/lme-fedora-niri-qs/pull/129
      (fix/materials-popup-blur; engine test green on the real machine; standalone probe verified
      scoped blur on live niri; LiquidNativeCase has 3 PRE-EXISTING env failures on the machine,
      identical on main — documented in the PR; if #129 merges after a Q5 branch exists, rebase
      Q5 — both touch shell.qml).
- [ ] Q5 leg 1: weather + lyrics — DESIGN COMPLETE (below), coding NOT started.
- [ ] Q5 leg 2: wallpaper family (wallpaper/wallpaper_actions/wallpaper_palette/gowall_actions/palette_actions, 486).
- [ ] Q5 leg 3: file_search + file_search_actions (72) + fileOpen + equalizer_actions + audio_visualizer (494).
- [ ] Q5 leg 4 (review-stop): clipboard (315) — wl-paste/wl-copy long-lived children; propose
      Process.startDetached + PDEATHSIG helper vs stays-Python; owner picks per review stop.
- [ ] Q5 close-out + archive records.

## Q5 leg 1 DESIGN (weather + lyrics) — frozen this session

Sources read: scripts/weather.py (208), weather_actions.py (48), lyrics.py (137);
tests/test_features.py::WeatherCase (auto-detect→forecast flow, geo backoff 120s, forecast
900s keep-last-good, manual fallback, unit switch hides stale), tests/test_lyrics.py +
test_lyrics_modes.py (parse corpus). QML consumers: qml/panels/WeatherWidget.qml (reads
ShellState.weather: location/available/automatic/loading/temperature/feelsLike/condition/
icon/unit/daily + ShellState.run("weatherRefresh")), qml/components/LyricsSession.qml
(spawns scripts/lyrics.py as a one-shot stdin/stdout worker; parses JSON result
{status, lines[], synced, plain, source, error}).

### Files to create (branch qml/q5-weather-lyrics off origin/main)

1. `qml/services/WeatherModel.js` (.pragma library): CONDITIONS table (verbatim from
   weather.py), location() validation (name 1-120, country ≤100, lat/long bounds, round 6),
   forecastParams(place, unit) (timezone auto, forecast_days 3, wind mph/kmh, current/daily
   field lists), normalizeForecast(data, unit, wallClock) (temperature finite check →
   'The weather service returned no valid temperature.', CONDITIONS lookup, daily ≤3 with
   per-key list validation → 'The weather service returned an invalid forecast. Retry.',
   unit/windUnit strings, updatedAt), normalizeSearch(data) (≤6 results, admin1 dedupe,
   'The location service returned an invalid response. Retry.'), detectLocation(data)
   ('Automatic location is unavailable. Retry or choose a city in Settings.' on success!=true).
2. `qml/services/WeatherState.qml` (singleton, pragma Singleton + qmldir): the client state
   machine with **an injectable loader** `property var loader` defaulting to XMLHttpRequest
   (test seam mirroring the Python opener injection): detect (ipwho.is, fields param),
   search (geocoding-api, count 6), forecast (api.open-meteo). Due scheduling by Date.now():
   geo 3600 ok / 120 fail; forecast 900 ok / 120 fail; key = (lat,lon,unit) change hides old
   data (matches = key === forecastKey gating in the snapshot builder). Snapshot section
   shape EXACTLY as weather.py::snapshot (available/configured/automatic/location/loading/
   stale/error/search{query,loading,results,error}). XHR deviation to document: responseText
   materializes before the 1 MiB post-hoc size check (open-meteo replies are ~10-50 KB).
   Errors → 'Weather service is unavailable. Check your connection and retry.'
3. `qml/services/LyricsModel.js`: parse(text) port (STAMP regex [m:ss(.xx)], offset tag,
   MAX_BYTES 512KiB via utf-8 byte estimate, MAX_LINES 4000 both raw and expanded, equal-time
   grouping with \n join + dedupe, plain fallback excluding [tag:] lines, utf-8-sig BOM strip),
   track(request) validation (title/artist/album 512, url 4096, embedded 512KiB, duration
   0-86400, online bool), result(text, source, instrumental) status machine
   (instrumental/ready/none + metadata/offline/error wrappers).
4. `qml/services/LyricsState.qml`: the native lookup flow replacing the LyricsSession worker:
   embedded → sidecar .lrc via FileView (file:// url, unquote, .with_suffix) → disk cache
   read via FileView → online XHR (lrclib.net/api/get, 404→{}, UA 'LME-Shell/2 (...)', 7s
   timeout) → cache store via helper. CACHE KEY CHANGE (no sha256 in QML): deterministic slug
   of [title,artist,album,duration]; cache JSON gains storedAt (epoch) because FileView has
   no mtime; TTLs 6h (status none) / 14d; old Python sha256 entries simply expire unread
   (documented). LyricsSession.qml keeps its cue scheduler; swap its Process worker for
   LyricsState.
5. `scripts/lyrics.py`: add bounded `--store` mode (stdin JSON {directory, filename, raw,
   status} → storage.write_json {storedAt, raw, status} + the 128-entry mtime maintenance) —
   the infra-helper pattern (idle_control.py precedent). The lookup path stays functional but
   gets DEPRECATED(Q5->Q6).
6. `shell.qml`: backend Process command gains `--no-weather` (backend stops fetching in real
   sessions — the --no-session-daemons precedent); ShellState.weather binds through
   NativeState.weather (the Q4 sections pattern); the router fan-out adds WeatherState
   (weatherSearch/weatherDetect/weatherRefresh/weatherSelect — select writes
   weatherLocation+weatherAutoLocation=false via the setting action).
7. `scripts/desktop_backend.py`: `--no-weather` flag (weather_fetch=False equivalent, real
   sessions only); weather section sites + weather.py/weather_actions.py/lyrics.py get
   DEPRECATED(Q5->Q6) markers.

### Tests (tests/test_native_weather_lyrics.py; new file, watch the 250 default cap → ratchet)

- Contract pins: shell.qml routes the four actions + --no-weather in the backend command;
  DEPRECATED(Q5->Q6) count on the three modules; WeatherState loader default shape;
  LyricsState's store-helper invocation (argv shape, not bare tokens); qmldir entries.
- Engine cases (real machine): WeatherModel corpus (CONDITIONS spot checks, location
  accept/reject, normalizeForecast happy + malformed daily + non-finite temperature,
  normalizeSearch admin1 dedupe + invalid, detect success/fail); WeatherState machine with a
  fake loader (auto-detect→forecast, geo failure 120s backoff, forecast failure keeps last
  good at 900s, manual location, unit switch hides stale — mirror WeatherCase); LyricsModel
  parse corpus (port test_lyrics.py cases: multi-stamp lines, offset, grouping, oversized
  rejection, plain fallback); LyricsState flow with fake loader + tmp cache + a real
  `lyrics.py --store` round trip.

### Verification flow (as Q4)

Sandbox G0 → push → real machine: worktree ~/glm-work/<branch>, venv pytest the new file +
test_features/test_lyrics* regression, qmllint, then PR. Live checks after owner merge:
weather panel refresh/search/select in Settings, lyrics on an MPRIS player.

## Standing rules (owner, 2026-11-12)

- Sub-agent prompts ALWAYS in English; provider opencode > openrouter; free models
  deepseek-v4.1-flash-free > nemotron-3-ultra-free; 2×1000 calls/day budget.
- Remote files under ~/glm-work/ ONLY; sweep /tmp strays; live shell never killed by us.
- OpenCode auth: /home/z/my-project/.oc-auth.b64 (curl --header @file); executor
  bash /home/z/my-project/scripts/oc.sh <timeout_ms> <command>; worktrees under ~/glm-work.
- Live shell env gotchas (learned this session): battery-saver.json active:true gates ALL
  blur off (temporarily flip + restore for blur tests); grim -c includes cursors (pointer
  verification: crop max=255 test); the shell IPC exists: `quickshell -p <config> ipc call
  shell toggle <panel>`; screenshots via magick stats (edge -edge 1 stddev) — means lie
  (scrim confounds); pull images by chunked base64 (oc.sh output page limit).
- niri 26.04 ext-background-effect: region → blur exactly there (empty region = no blur;
  unset vs set semantics in src/handlers/background_effect.rs); niri cannot run headless
  (winit/DRM only — private sessions use Sway, which lacks the blur protocol).
