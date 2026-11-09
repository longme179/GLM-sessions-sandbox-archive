# Route 1 — GLM self-audit of annotations on `docs/annotate-and-map`

Date: 2026-11-09. Auditor: GLM (main agent), fully local replica method:
`git clone main @ 6c1dc3c` + byte-identical patch replay (md5 `9ad76afc5ba63fc74e8b81084f79bea6`)
of `git diff main..docs/annotate-and-map` (445 files, +1515/−312).

## Method (verification-before-completion, per superpowers)
- Mechanical claim extraction: tolerant REL grammar parser (multi-target, `::symbol`,
  `(.qsb)` suffix, bare-filename resolution incl. comma-list dir inheritance).
- Every claim checked by code command, not by reading the map's own words.
- Independent re-run of the no-behavior-change battery (not trusting prior session logs).

## Verified CLEAN (evidence)
| Check | Result |
|---|---|
| REL path references (~180 across 108 tag lines) | 180/180 resolve to real files |
| REL `::symbol` references | 5 wrong / ~180 (see findings) |
| INVARIANT (26) + GOTCHA (10) semantic review | all TRUE; deep spot-checks: storage atomic write (temp+fsync+os.replace), launchpad bash-only-when-kind, NIRI_SOCKET scoping, Pair 120000ms, ActionSpec fields exact (name,contexts,live,demo,execution,complete,presentation,prepare), backend_providers fail-closed, niri_events 8MB buffer cap, one-completion-per-cycle sequence |
| Action-name pairing (wifiToggle/lock/bluetoothToggle/batterySaver/launchpadRun) | all in the tagged provider files |
| Map file:line refs (34) | 34/34 path exists + line in range |
| Map content anchors (~40 checked: shell.qml:18-26, ShellState.qml:158-230, desktop_backend.py:34-1679, FeatureCatalog.qml:154, ControlRegistry.qml:21-26, backend_actions.py:13-75, run-gates.sh:36-83, clipboard.py:159/230, popup-jelly.vert:3-4, test_settings_startup.py:153, deploy*.py, AGENTS.md sections) | all match branch content, EXCEPT check_architecture.py anchors (finding F) |
| No-behavior-change: Python (276 files) | ast.dump minus docstrings byte-identical main↔branch |
| No-behavior-change: QML/JS/frag/vert (153) | string-aware comment strip + ws-normalize identical |
| No-behavior-change: .sh (14) | added lines are comments only, zero removals |
| Other files | only AGENTS.md (+4 pointer) + docs/WORKSPACE_MAP.md (new); no .json/.qsb/vendor touched |
| `python3 scripts/check_architecture.py` on branch | PASSES (ratchet intact) |
| `python3 -m compileall scripts tests` | clean |
| AGENTS.md Phase-5 pointer (read map / grep REL / update on change / `git diff 6c1dc3c..HEAD --stat`) | present, exact |
| Branch hygiene | clean tree, no upstream (not pushed) |

## FINDINGS (hallucination-class or quality)
| # | Location | Claim | Reality | Class |
|---|---|---|---|---|
| A | qml/services/ControlRegistry.qml:2 | `scripts/feature_catalog.py::read_control_grid` | No such symbol; control-grid.json is read by `legacy_ids()` (l.97) / `load_catalog()` (l.119). Relationship itself true. | invented symbol |
| B | qml/settings/SettingsRegistry.qml:3 | `qml/settings/SettingsView.qml::openPage` | `openPage` is defined in qml/settings/SettingsApplication.qml:23 (IpcHandler); SettingsView has `navigate`. Relationship true (openPage consults SettingsRegistry.page). | wrong file |
| C | scripts/deploy_niri.py:5 | `scripts/deploy_niri_tree.py::parse/validate paths` | `parse` does not exist; real API: `graph()`, `validate()`. | loose/misnamed symbol |
| D | scripts/check.sh:3 | `REL: tests/, migration gates` | No concrete path/symbol form ("migration gates" = concept; tests/ = directory). Tag not machine-checkable. | vague tag |
| E | qml/panels/ControlDashboard.qml:217 | `scripts/audio_actions.py::provide – "powerProfile"` | `powerProfile` is handled in scripts/desktop_backend.py (l.1359/1422/1475), not audio_actions.py. Sibling tag :159 bluetoothToggle is correct. | wrong file |
| F | docs/WORKSPACE_MAP.md (§1, §7, §9) | `check_architecture.py:152-155` / `:152` / `:1-164` for largeFiles ratchet | Baseline-pinned numbers: on the annotated branch the file is 170 lines and largeFiles enforcement is at 159-161 (comments added above shifted lines). All other map anchors match branch state → internally inconsistent. | stale line anchor |

Minor observations (not counted as failures):
- scripts/action_pending.py:5 uses non-standard `::run,::backend` double-symbol shorthand (both symbols exist).
- tests/*.py headers are template-generated ("Contract/helper: test infrastructure for <self-name>") — accurate but mechanical.
- Map §6 flow (e) (prewarm/warm-render) is honestly marked [inferred]; §10 finding rows verified where checkable.

## Verdict (Route 1)
- Path accuracy: **100%** (180/180)
- Symbol/relationship accuracy: **~97%** (5 defective of ~180; A/B/E are true hallucination-class: invented name or wrong file; C/D are loose syntax)
- Map: structurally complete (11/11 sections), refs valid, one stale-anchor cluster (F)
- No-behavior-change: **PROVEN independently** (0 failures across 443 code files + 2 doc files)
- Overall: annotations are overwhelmingly real, with 5 pinpoint defects worth fixing in a follow-up comment-only commit (and 1 map anchor refresh).
