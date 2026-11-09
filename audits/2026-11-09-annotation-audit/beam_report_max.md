# Audit: code annotations vs code (docs/annotate-and-map)

Branch: docs/annotate-and-map (base 6c1dc3c). Read-only audit.

## Totals
- REL: 108 tags checked
- INVARIANT: 26 tags checked
- GOTCHA: 10 tags checked
- TOTAL tags: 144

## Verdict counts
- REL: PASS 103, FAIL 2, PARTIAL 3, UNVERIFIABLE 0
- INVARIANT: PASS 26, FAIL 0, PARTIAL 0, UNVERIFIABLE 0
- GOTCHA: PASS 10, FAIL 0, PARTIAL 0, UNVERIFIABLE 0

## FAIL / PARTIAL (REL only)

1. FAIL — qml/settings/SettingsRegistry.qml:3
   Claim: REL target `qml/settings/SettingsView.qml::openPage`
   Wrong: SettingsView.qml has no `openPage`. It is defined in `qml/settings/SettingsApplication.qml:23`.
   Evidence: `grep -rn "openPage" qml/settings/` -> SettingsApplication.qml:23 only.

2. FAIL — qml/services/ControlRegistry.qml:2
   Claim: REL target `scripts/feature_catalog.py::read_control_grid`
   Wrong: no `read_control_grid` symbol anywhere; only annotation itself.
   Evidence: `grep -rn "read_control_grid" .` returns only ControlRegistry.qml:2.

3. PARTIAL — scripts/deploy_niri.py:5
   Claim: `scripts/deploy_niri_tree.py::parse/validate paths`
   Partial: `validate` exists (deploy_niri_tree.py defines `validate`), but no `parse`.
   Evidence: `grep -n "^def " scripts/deploy_niri_tree.py` -> included, graph, replace, validate; no parse.

4. PARTIAL — scripts/deploy_niri_tree.py:5
   Claim: `scripts/deploy_niri.py::planning`
   Partial: function is `plan` (deploy_niri.py:91), not `planning`.
   Evidence: `grep -n "^def " scripts/deploy_niri.py` -> normalized, legacy_include, competing, fragment, plan.

5. PARTIAL — scripts/backend_providers.py:6
   Claim: `scripts/backend_actions.py::ActionRegistry.provide`
   Partial: class and method exist separately, but the combined `ActionRegistry.provide` token is absent (grep -nw returns no match).
   Evidence: `grep -n "class ActionRegistry\|def provide" scripts/backend_actions.py` -> both present; `grep -nw 'ActionRegistry.provide'` -> none.

Bare filenames in REL tags were resolved by sibling/tagging-file directory (e.g. `NotificationCenter.qml` via sibling `qml/panels/NotificationToasts.qml`; deploy helpers via scripts/ directory). All resolved files exist.

## INVARIANT / GOTCHA
All 26 INVARIANT and 10 GOTCHA claims match surrounding code and docs (access/bounds/worker scoping/atomic writes/registry uniqueness/timeout values, etc.). No failures found.

## WORKSPACE_MAP.md check
- Unique file:line references checked: 55
- Resolution: all basic/cross (bare basenames) resolved uniquely to existing files.
- Bounds: all line numbers within file bounds (including ranges).
- Content: sampled anchors match map claims (shell.qml:18-26, ShellState.qml:158/171/230, desktop_backend.py:34/504/553-554/1172/1182/1194/1197/1209/1341-1342/1365/1638/1679, check_architecture.py, run-gates.sh, FeatureCatalog/ControlRegistry/SettingsView lines). No bad refs list after resolution.
- [verified] rows spot-checked: module entries and findings point to real file:line and code (e.g. tests/test_settings_startup.py:153).
- Minor offset note: map cites check_architecture.py "ratchet" at 152-155; size ratchet error lines are 156-161, though 152 begins the legacy/cycle handling context. Not a hard mismatch.

## Comments-only check
`git diff 6c1dc3c..HEAD --numstat`: 445 files changed, +1515/-312.
All changed hunks inspected are comments/docstrings/headers/REL/INVARIANT/GOTCHA tags appended or docstrings reformatted from single-line to multi-line. No executable statements changed. No file with real code touched identified.

## Overall conclusion
Annotations are substantial and mostly accurate, but not fully hallucination-free: 5 REL issues found (2 definitely wrong targets/symbols, 3 qualified-name partials). INVARIANT/GOTCHA and map references are sound; diff is comments/docs only. Fix the 5 REL items before merge.