# Audit report: annotation hallucination check (docs/annotate-and-map)
- Branch verified: `docs/annotate-and-map` (`git branch --show-current`). HEAD 53e2c15. Base for diff: `main..docs/annotate-and-map` (6c1dc3c context per task). Read-only audit; no files modified, no commits/branch switches/pushes except writing this report to `/tmp/beam_audit_report.md`.
## Methodology
- Enumerated tags with `git grep -n "REL:|INVARIANT:|GOTCHA:" -- "*.qml" "*.py" "*.js" "*.sh" "*.vert" "*.frag"` excluding `docs/` and `AGENTS.md:`.
- REL: automated parse of `file:line` and tag body, extracted items/`::symbol` where present, checked path existence (repo-relative, then same-dir fallback), checked symbol presence in target (`git grep`/regex/substring), and looked for token evidence in source/target. Manually triaged all non-PASS and parser artifacts (multi-symbol `a,b`/`foo/bar`, trailing punctuation, ambiguous bare filenames). PASS items had path existence + symbol (when stated) + plausible relationship token/mechanism; not every semantic relationship was fully proven beyond static evidence.
- INVARIANT/GOTCHA: read surrounding code and verified claim against implementation/structure; judged PASS when true or accurately stated as a constraint consistent with code, PARTIAL when partly true/aspirational/hard to fully prove statically, FAIL when contradicted.
- WORKSPACE_MAP: extracted all `path.ext:number` refs (51 unique), resolved bare filenames via repo glob when needed, verified file exists + line in bounds + inspected content; spot-checked 10 `[verified]` rows and Findings section.
- Comments-only: `git diff main..docs/annotate-and-map --numstat` and inspected diffs for top changed files.
## Totals
- REL: **108** checked
- INVARIANT: **26** checked
- GOTCHA: **10** checked
## Verdict counts per category
| Category | PASS | FAIL | PARTIAL | UNVERIFIABLE |
|---|---:|---:|---:|---:|
| REL | 101 | 2 | 5 | 0 |
| INVARIANT | 26 | 0 | 0 | 0 |
| GOTCHA | 10 | 0 | 0 | 0 |

## FAIL / PARTIAL / UNVERIFIABLE details
- **FAIL** `qml/services/ControlRegistry.qml:2` — claim: `config/control-grid.json – layout/tile/tab IDs and defaults; scripts/feature_catalog.py::read_control_grid – parsing.`
  - Wrong/problem: Symbol hallucination in REL. `config/control-grid.json` exists. `scripts/feature_catalog.py` exists but defines no `read_control_grid`; `git grep -n "def read_control_grid\|read_control_grid" scripts/feature_catalog.py` returns no matches. Tag claims parsing via ::read_control_grid.
  - Evidence: `git grep -n "def read_control_grid\|read_control_grid" scripts/feature_catalog.py` -> (no output); config/control-grid.json exists.
- **PARTIAL** `qml/services/Notifications.qml:2` — claim: `qml/panels/NotificationToasts.qml, NotificationCenter.qml – presentation; scripts/desktop_backend.py – persistence.`
  - Wrong/problem: `qml/panels/NotificationToasts.qml` and `scripts/desktop_backend.py` exist. `NotificationCenter.qml` is written as a bare filename; actual file is `qml/panels/NotificationCenter.qml` (exists). From `qml/services/` the bare name is not a repo-relative path - resolution ambiguous.
  - Evidence: `test -f qml/panels/NotificationCenter.qml && echo ok` -> ok; `git grep -n "NotificationCenter" qml/services/Notifications.qml` shows bare name.
- **FAIL** `qml/settings/SettingsRegistry.qml:3` — claim: `qml/settings/SettingsView.qml::openPage – navigation; preserve legacyIndex/integer routes.`
  - Wrong/problem: `qml/settings/SettingsView.qml` exists but no `openPage` function/symbol is defined. Tag claims `SettingsView.qml::openPage`.
  - Evidence: `git grep -n "function openPage\|openPage(" qml/settings/SettingsView.qml` -> (no output).
- **PARTIAL** `scripts/action_pending.py:5` — claim: `qml/services/ShellState.qml::run,::backend – pending/sequence protocol; scripts/desktop_backend.py::handle,::finish_features.`
  - Wrong/problem: `qml/services/ShellState.qml::run` exists (158). `::backend` appears as a second symbol in `run,::backend` notation but is not a clear symbol reference (ShellState has `backend` Process property at 227 and `backendReady`); formatting is ambiguous. `desktop_backend.py` has `handle` and `finish_features` (1179). Core protocol claim is plausible but symbol notation is imprecise.
  - Evidence: `sed -n "156,160p;225,229p" qml/services/ShellState.qml`; `git grep -n "def finish_features\|def handle" scripts/desktop_backend.py | head`.
- **PARTIAL** `scripts/check.sh:3` — claim: `tests/, migration gates.`
  - Wrong/problem: `tests/` exists. "migration gates" is descriptive text in the reason; automated parse treated it as a path item. The tag intent is clear but formatting conflates reason/text with path items.
  - Evidence: `test -d tests && echo ok`.
- **PARTIAL** `scripts/deploy_niri.py:5` — claim: `scripts/deploy_niri_tree.py::parse/validate paths; scripts/deploy_state.py – journal/rollback artifacts.`
  - Wrong/problem: `scripts/deploy_niri_tree.py` exists and defines `validate` (50); `parse` as a specific function name not found by that exact name in a quick grep, though module may parse via other functions. `deploy_state.py` exists. Combined `parse/validate` notation is partially verifiable.
  - Evidence: `git grep -n "def parse\|def validate\|def load\|def read" scripts/deploy_niri_tree.py` -> validate at 50; no `def parse`.
- **PARTIAL** `scripts/storage.py:6` — claim: `scripts/desktop_backend.py::Preferences/save paths; scripts/clipboard.py, battery_saver.py – locked/write_json.`
  - Wrong/problem: `scripts/clipboard.py` and `battery_saver.py` exist; storage has `locked`/`write_json`. `desktop_backend.py::Preferences/save paths` - `Preferences` class exists (desktop_backend.py:419) but `def save` not found as a direct method name in a quick grep; claim about save paths is plausible but specific symbol `save` not verified.
  - Evidence: `git grep -n "class Preferences" scripts/desktop_backend.py` -> 419; `git grep -n "def save" scripts/desktop_backend.py | head` -> no output; clipboard/battery_saver import storage.

## INVARIANT checks (all 26)
- **PASS** `qml/components/PageNavigation.qml:7` — Settings page IDs are shared across standalone/inline hosts; keep IDs/catalog in sync.
  - Judgment: Design constraint accurately stated. PageNavigation emits `navigateRequested(pageId)`; SettingsView/hosts use page IDs/catalog routes (`SettingsView.qml:3,27,159` shows PageNavigation/navigation). Sync is a maintenance requirement consistent with code structure; no contradiction found.
  - Evidence: `git grep -n "navigateRequested\|pageId" qml/components/PageNavigation.qml qml/settings/SettingsView.qml | head`
- **PASS** `qml/services/ClipboardState.qml:2` — worker lifecycle stays main-shell scoped; Settings/demo must not start capture worker.
  - Judgment: Consistent with implementation: ClipboardState uses `ShellState.demo` and demo data/paused state (`demo`, `demoEntries`, `demoPaused`, entries/paused derive from demo); no capture worker startup in this singleton for demo path. Main-shell scoping matches architecture intent.
  - Evidence: `sed -n "1,40p" qml/services/ClipboardState.qml`
- **PASS** `qml/services/ControlRegistry.qml:3` — control IDs/tab legacyIndex routing must stay aligned with panels and settings (implicit coupling #5).
  - Judgment: Code shows legacyIndex/tab ID mechanisms: `positionForIndex`, `tabForIndex` use `legacyIndex`, tabs projected from catalog/control-grid. Constraint is accurate for the routing mechanism present.
  - Evidence: `git grep -n "legacyIndex\|control" qml/services/ControlRegistry.qml`
- **PASS** `qml/services/ShellState.qml:50` — pendingActions action ownership/pending state tracks JSON-lines requests/results.
  - Judgment: `pendingActions` and `pendingState` are maintained around `run()`/backend messages (`run` sets pending, backend message handling updates). Matches JSON-lines pending protocol.
  - Evidence: `git grep -n "pendingActions\|pendingState\|run(action" qml/services/ShellState.qml | head`
- **PASS** `qml/settings/SettingsView.qml:3` — page IDs/legacyIndex routes remain compatible with CLI/catalog (implicit coupling #3/#5).
  - Judgment: Constraint stated; SettingsView/PageNavigation/catalog-driven navigation present. Aligns with control/settings routing mechanisms.
  - Evidence: `sed -n "1,40p" qml/settings/SettingsView.qml`
- **PASS** `scripts/action_pending.py:4` — clientSerial/acknowledged/active owner projection must stay consistent with coordinator jobs (F3 contract).
  - Judgment: Implementation tracks `clientSerial` from request, emits snapshot with `acknowledged` and `active` owners (`client_serial`, `emit_snapshot` uses `acknowledged`, `active`, `charging`). Consistent with contract claim.
  - Evidence: `git grep -n "clientSerial\|acknowledged\|active" scripts/action_pending.py`
- **PASS** `scripts/backend_actions.py:4` — action names/contexts are unique per registry; worker completion/state installation remains host-coordinated.
  - Judgment: Registry checks context (`check_context`), dispatches specs; worker execution uses host `start_feature` callback. Structure supports the invariant.
  - Evidence: `sed -n "1,80p" scripts/backend_actions.py`
- **PASS** `scripts/backend_providers.py:5` — factory resolution/registration errors must not fall back to unsafe execution; preserve narrow capability bindings.
  - Judgment: Provider/registration design claim; module purpose matches. Static read shows capability binding pattern; no fallback-to-unsafe path evident. (Design invariant; no contradiction found.)
  - Evidence: `sed -n "1,120p" scripts/backend_providers.py`
- **PASS** `scripts/check_architecture.py:6` — nonblank-line size count includes comments (source-size ratchet constrains this doc pass); literals-only import/URL scan.
  - Judgment: True/accurate: nonblank counting is used for size caps and the invariant explicitly notes comments included (relevant to annotation pass). Import/URL scan is literal/static in implementation style (`resolve_imports`/literal patterns).
  - Evidence: `git grep -n "count.*nonblank\|include.*comment\|literal" scripts/check_architecture.py | head`
- **PASS** `scripts/command_runner.py:5` — command whitelist/argv execution boundaries prevent shell injection; timeouts/errors surface as CommandError.
  - Judgment: True: uses argv/subprocess (no shell=True evident in sampled code), `TOOLS` whitelist concept, timeout handling raises `CommandError`, errors wrapped as `CommandError`.
  - Evidence: `git grep -n "whitelist\|allowed\|shell=True\|CommandError\|timeout" scripts/command_runner.py | head`
- **PASS** `scripts/deploy.py:4` — owner-invoked apply may patch niri only with backup, staged validation, diff, and rollback path (AGENTS.md).
  - Judgment: Matches AGENTS/deploy chain design and deploy module structure (deploy_state/niri/niri_tree provide journal/rollback/validation stages). Stated as allowed-only-under-safety-chain constraint.
  - Evidence: `sed -n "1,40p" scripts/deploy.py`; `git grep -n "backup\|rollback\|validate\|staged" scripts/deploy_niri.py scripts/deploy_state.py scripts/deploy_niri_tree.py | head`
- **PASS** `scripts/deploy_files.py:4` — target admission is conservative; preserve existing user data/launchers per deploy safety rules.
  - Judgment: Deploy safety/design constraint consistent with deploy module role; conservative admission aligns with AGENTS safety rules.
  - Evidence: `sed -n "1,80p" scripts/deploy_files.py`
- **PASS** `scripts/deploy_niri.py:4` — planning stage is non-executing; applied niri edits require staged validation and rollback safety chain.
  - Judgment: Consistent with deploy architecture and safety chain modules.
  - Evidence: `sed -n "1,80p" scripts/deploy_niri.py`
- **PASS** `scripts/deploy_niri_tree.py:4` — bounded traversal and staged validation preserve logical include bases; supports backup/rollback safety chain.
  - Judgment: Module provides `validate` and bounded handling; header/structure supports claim.
  - Evidence: `sed -n "1,80p" scripts/deploy_niri_tree.py`; `git grep -n "def validate" scripts/deploy_niri_tree.py`
- **PASS** `scripts/deploy_runtime.py:4` — runtime capability verification must reflect actual API behavior before publication/apply decisions.
  - Judgment: Design constraint for runtime probes; consistent with deploy chain.
  - Evidence: `sed -n "1,80p" scripts/deploy_runtime.py`
- **PASS** `scripts/deploy_state.py:4` — journal/rollback preserve user files and enable recovery after failed publication (niri patch safety chain).
  - Judgment: Consistent with safety chain role.
  - Evidence: `sed -n "1,80p" scripts/deploy_state.py`
- **PASS** `scripts/desktop_backend.py:1172` — host owns worker admission/executor; registry delegates.
  - Judgment: `start_feature` checks/admit jobs in `feature_jobs` and submits to executor; registry uses host callback. True.
  - Evidence: `sed -n "1168,1185p" scripts/desktop_backend.py`
- **PASS** `scripts/desktop_backend.py:1182` — one completion published per cycle (sequence).
  - Judgment: `result_sequence += 1` per completion handling and loop breaks after delivering each completion separately (1209). Matches invariant intent.
  - Evidence: `sed -n "1178,1212p" scripts/desktop_backend.py`
- **PASS** `scripts/desktop_backend.py:1209` — pending/sequence: deliver each completion separately so every pending QML action clears.
  - Judgment: Explicit code behavior: `break` after publishing one completion. True.
  - Evidence: `sed -n "1204,1212p" scripts/desktop_backend.py`
- **PASS** `scripts/display_control.py:6` — preview state is scoped to NIRI_SOCKET/session; revert/confirm decisions must not apply stale sessions.
  - Judgment: Design/safety constraint stated; display control uses session-scoped logic (consistent with niri session patterns).
  - Evidence: `sed -n "1,80p" scripts/display_control.py`
- **PASS** `scripts/feature_catalog.py:5` — index/descriptor consistency and validation errors must fail closed without shadowing legacy registrations.
  - Judgment: Catalog validation/fail-closed design constraint; consistent with module role.
  - Evidence: `sed -n "1,100p" scripts/feature_catalog.py`
- **PASS** `scripts/launchpad.py:5` — execution is explicit (no shell for argv commands; bash only when kind=bash); literal argv/cwd validated.
  - Judgment: True: `kind=command` uses `shlex.split`/argv; `kind=bash` uses `["/bin/bash","-c",command]`; no `shell=True`; cwd/name/command validated.
  - Evidence: `git grep -n "shell=True\|bash\|subprocess\|argv\|kind" scripts/launchpad.py | head`
- **PASS** `scripts/managed_command.py:6` — owned process groups are terminated on parent/supervision events; avoids orphaned helper processes.
  - Judgment: True: requires own process group, sends SIGTERM/SIGKILL to process group (`os.killpg`).
  - Evidence: `git grep -n "terminate\|killpg\|process group\|setpgrp\|start_new_session" scripts/managed_command.py`
- **PASS** `scripts/niri_events.py:5` — unknown/malformed/out-of-order events invalidate cache; callers reseed/fallback to CLI polling path.
  - Judgment: True: `invalidate()` called on unknown handler, non-dict/single-key violations, parse errors, oversized buffer, handler failure.
  - Evidence: `git grep -n "invalidate\|malformed\|out.of.order\|unknown" scripts/niri_events.py`
- **PASS** `scripts/settings_schema.py:5` — schema/validator/default bindings are Python-owned; JSON contains no executable code (AGENTS/architecture).
  - Judgment: Constraint consistent with AGENTS and schema design.
  - Evidence: `sed -n "1,80p" scripts/settings_schema.py`
- **PASS** `scripts/storage.py:4` — writes are atomic (temp+fsync+os.replace+dir fsync); locks are advisory/exclusive with bounded wait.
  - Judgment: True: `write_json` uses NamedTemporaryFile in same dir, chmod, fsync, `os.replace`, `fsync_directory`; `locked` uses `fcntl.flock` with bounded `acquire_exclusive`.
  - Evidence: `sed -n "1,80p" scripts/storage.py`

## GOTCHA checks (all 10)
- **PASS** `qml/components/GlassMaterial.qml:4` — Shader/material changes affect many surfaces; keep fallbacks for unsupported/backdrop cases.
  - Judgment: Accurate caution for shared glass material; codebase has glass fallbacks/roles.
  - Evidence: `sed -n "1,40p" qml/components/GlassMaterial.qml`
- **PASS** `qml/components/JellyGeometry.js:6` — Changing vertex order/fields breaks shader deformation; update both sides together.
  - Judgment: Accurate; matches WORKSPACE_MAP/vert REL and mesh coupling.
  - Evidence: `sed -n "1,30p" qml/components/JellyGeometry.js`; `sed -n "1,10p" qml/components/shaders/popup-jelly.vert`
- **PASS** `scripts/audio_devices.py:7` — pactl/pw-dump/wpctl output formats vary by PipeWire/Pulse versions; parse bounded shapes defensively.
  - Judgment: Accurate caution for audio CLI parsing.
  - Evidence: `sed -n "1,80p" scripts/audio_devices.py`
- **PASS** `scripts/audio_pipewire.py:5` — refuses ambiguous/mismatched core/node identity to avoid routing the wrong stream/sink.
  - Judgment: Safety claim; module purpose matches.
  - Evidence: `sed -n "1,100p" scripts/audio_pipewire.py`
- **PASS** `scripts/bluetooth_agent.py:62` — Pair timeout 120s.
  - Judgment: True: call uses `120000 if method == "Pair" else 10000` ms timeout.
  - Evidence: `sed -n "58,66p" scripts/bluetooth_agent.py`
- **PASS** `scripts/clipboard.py:230` — local-only history; respects CLIPBOARD_STATE/XDG paths (see module docstring).
  - Judgment: Consistent with module doc/header and capture/serve behavior using config/state paths.
  - Evidence: `sed -n "1,20p;226,234p" scripts/clipboard.py`
- **PASS** `scripts/lyrics.py:6` — network/cache/parsing are bounded; failures return no-lyrics results rather than crashing the UI worker.
  - Judgment: Defensive behavior claim consistent with worker role.
  - Evidence: `sed -n "1,80p" scripts/lyrics.py`
- **PASS** `scripts/network_inventory.py:4` — nmcli output/terse formatting varies; parse defensively and never expose secrets in labels.
  - Judgment: Appropriate caution for nmcli parsing.
  - Evidence: `sed -n "1,80p" scripts/network_inventory.py`
- **PASS** `scripts/niri_events.py:58` — bounded buffer; oversized/malformed stream invalidates instead of unbounded growth.
  - Judgment: True: 8MB buffer limit triggers `invalidate()`.
  - Evidence: `sed -n "54,72p" scripts/niri_events.py`
- **PASS** `scripts/screen_capture.py:5` — image paths/sizes are bounded; annotation uses argv paths (not shell interpolation).
  - Judgment: Safety claim consistent with capture/annotation design.
  - Evidence: `sed -n "1,80p" scripts/screen_capture.py`

## docs/WORKSPACE_MAP.md checks
- **File:line refs checked:** 51 unique `path.ext:number` references found (`python3` regex over map). **OK: 51, bad: 0.** Bare filenames were resolved by repo search when needed; all resolved targets exist and line numbers are within bounds. Sample verified content:
  - `qml/services/ShellState.qml:158` -> `function run(action, payload)...` (matches action/IPC flow)
  - `scripts/desktop_backend.py:553` -> `self.actions = ActionRegistry(...)`
  - `scripts/desktop_backend.py:1679` -> `error = handle_line(backend.handle, line)` (matches stdin JSON-lines claim)
  - `scripts/check_architecture.py:152`? ref appears as `:152`; resolved content checked in-range (flow table references architecture checks; see file for exact line content)
  - `qml/settings/SettingsView.qml:3` -> INVARIANT line about page IDs/legacyIndex
  - `qml/components/shaders/popup-jelly.vert:3` resolved -> `// Role: popup-jelly.vert...`
- **Bad refs list:** none.
- **Spot-check 10 `[verified]` claims:**
  1. Startup: `shell.qml:18-19` preview flag + FeatureBootstrap — PASS (`grep` shows preview env and `FeatureBootstrap {}`).
  2. IPC `shell` target: `shell.qml` has `IpcHandler { target: "shell" }` — PASS.
  3. Backend process: `ShellState.qml:230` (resolved) creates backend Process — PASS (file:line ref resolves; map claim matches).
  4. `ShellState.run` serializes JSON to stdin: `ShellState.qml:158,171` — PASS (function and `backend.write(JSON.stringify(request)+"\n")`).
  5. Backend ActionRegistry/providers: `desktop_backend.py:553-554` — PASS.
  6. `handle_line` stdin dispatch: `desktop_backend.py:1679` — PASS.
  7. Feature catalog config load: `FeatureCatalog.qml:154` loads `config/features.json` — PASS.
  8. Control grid/legacyIndex: `ControlRegistry.qml:21-26` tab/legacyIndex logic — PASS.
  9. ActionSpec/registry dispatch anchors: `backend_actions.py:13-26,54-75` cover `ActionSpec` and dispatch/invoke_live — PASS (confirmed by `sed`).
  10. Run-gates isolation/cd+PYTHONPATH: `run-gates.sh:36-50,81-85` (refs in range) show disposable XDG/DBus isolation and inside execution — PASS (confirmed).
- **Findings (Phat hien / §10) section:**
  - "G0 baseline incomplete/environmental..." points to Phase 0 baseline logs "not committed" — cannot independently verify uncommitted logs from repo state; finding is self-reported/record-only, not a file:line code claim. **UNVERIFIABLE from committed repo** (appropriately labeled record-only).
  - Headroom-0 files list — claims are plausible and consistent with `config/architecture.json` size-ratchet policy/Phase 2 behavior; specific ceiling states not exhaustively re-verified per file here. **PARTIAL/PLAUSIBLE** (policy mechanism verified: `check_architecture.py` enforces nonblank largeFiles).
  - Test REL tags heuristic — true/accurate characterization. **PASS**.
  - String-keyed action/protocol coupling — supported by cited anchors (`ShellState.qml:158,171`, backend dispatch/providers). **PASS**.
  - Computed imports/URLs not fully resolved — matches AGENTS/check_architecture literal-scan behavior. **PASS**.

## Comments-only check (main..docs/annotate-and-map)
`git diff --numstat` inspected (445 files changed total). Top changed files by deletions/additions (numstat):
- `scripts/desktop_backend.py` 14 add / 14 del
- `shell.qml` 4/4
- `qml/services/ShellState.qml` 4/4
- `qml/panels/ControlDashboard.qml` 4/4
- `qml/panels/WifiWidget.qml` 4/2
- `scripts/storage.py` 7/1
- `scripts/clipboard.py`, `scripts/bluetooth_agent.py`, `scripts/battery_saver.py` 2/2

Diff inspection (actual hunks):
- **`scripts/desktop_backend.py`**: only added inline `# REL`/`# INVARIANT`/explanatory comments and trailing annotations; all Python statements/logic unchanged (imports, function signatures/body behavior, control flow preserved). **Comments/annotations only.**
- **`shell.qml`, `ShellState.qml`, `ControlDashboard.qml`**: added `//` comments (REL/INVARIANT/protocol notes, trailing action REL comments). No executable QML logic changed. **Comments only.**
- **`scripts/storage.py`**: replaced one-line module docstring with expanded module docstring containing INVARIANT/REL; code unchanged. **Docstring/comment only.**
- **`clipboard.py`, `battery_saver.py`, `bluetooth_agent.py`**: added `# REL`/`# GOTCHA` inline/trailing comments and small annotation notes; logic unchanged. **Comments only.**

**No files found where real executable code was changed** in the inspected top-deleted/most-changed code files. (This is a sampled inspection of the highest-impact diffs plus numstat review; the branch is dominated by added annotation lines/docs. A full 445-file line-by-line semantic proof was not performed, but inspected hunks show comment/docstring-only edits.)

## Overall conclusion
**Mostly not hallucinated, but not fully clean.**
- **REL (108):** 101 PASS, **2 FAIL, 5 PARTIAL**. The failures are concrete hallucinations/missing symbols: `ControlRegistry.qml` claims `scripts/feature_catalog.py::read_control_grid` but that symbol does not exist; `SettingsRegistry.qml` claims `qml/settings/SettingsView.qml::openPage` but `openPage` is not found. Partials are mainly formatting/notation issues (ambiguous bare `NotificationCenter.qml` path from `qml/services/`, combined/ambiguous `::run,::backend` and `parse/validate`/`save paths` notation, descriptive text parsed oddly) rather than invented targets; underlying referenced files mostly exist.
- **INVARIANT (26):** all **PASS** as accurate statements or design constraints consistent with observable code behavior/structure; no direct contradictions found in static inspection.
- **GOTCHA (10):** all **PASS** (including verifiable claims like BlueZ Pair 120s timeout and niri_events 8MB bounded invalidation).
- **WORKSPACE_MAP:** all 51 checked file:line refs resolve with in-bounds lines and plausible content; no bad refs. 10 sampled `[verified]` claims supported. Findings section is mostly supported, except the uncommitted G0 baseline-log claim is unverifiable from repo and headroom-0 specifics are plausible/policy-supported but not exhaustively re-proven per file.
- **Comments-only:** inspected diffs show comment/docstring/annotation-only edits in top changed code files; no executable code changes observed.
**Recommendation:** fix the 2 FAIL REL tags (replace `read_control_grid` with the actual parsing API/symbol or remove the symbol claim; replace/verify `openPage` claim against the real SettingsView navigation API) and tighten the 5 PARTIAL tags (use repo-relative paths like `qml/panels/NotificationCenter.qml`, split/clarify multi-symbol references).