# Session 2026-11-24 (Agent-2, GLM): Settings blank + CC stalls + caps lifted

Outcome: PR https://github.com/longme179/lme-fedora-niri-qs/pull/197
(branch fix/settings-blank-and-tab-prewarm, commit 0eb4ff4, base 7bfce04).

## Root causes (audit BEFORE fix, per owner order)
1. **Settings app blank** — PR #196's new PageHost binds its inner Loader to
   `height: root.height`, but SettingsView's `pageLoader` PageHost (an Item in a
   Flickable contentItem) has NO height of its own -> 0 px -> every page 0 px tall.
   The previous session discovered this at its very end (last messages mention
   "blank Settings page" regression check) and left an uncommitted height fix.
2. **CC tab microfreezes** — first visit to each tab built synchronously on the
   click (~100-700 ms). Previous session's fix attempt (asyncVisits +
   FrameAnimation pump) was wrong: frame pumps keep the render loop (glass blur)
   hot, and async incubation only advances on rendered frames -> stalls in idle
   scenes (their own finding, stashed as WIP).
3. **Limits** — largeFiles ceilings (config/architecture.json +
   check_architecture.py size-cap/ratchet) + per-test nonblank asserts +
   maxPages LRU caps (PageHost 6, PanelStage 4, SettingsView 6).

## Fixes shipped
- SettingsView.qml: `height: item ? item.implicitHeight : pageScroll.height`
  (all settings pages are ColumnLayout roots -> implicitHeight always computed).
- ControlCenter.qml: warm-up Timer (350 ms stagger) prebuilds every unvisited
  tab via new `PageHost.preload()`; clicks only switch built pages.
  refreshControls kept its pinned per-open/tab/reconnect contract (a 5 s
  throttle broke `controls_refresh` contract tests -> removed).
- Caps lifted: largeFiles deleted; check_architecture size loop removed;
  maxPages 6/4/6 -> 0/0/0; AGENTS.md/STATE.md/WORKSPACE_MAP.md policy updated.
- New regression test tests/test_instant_ui_regression.py (3 tests, green) —
  note: tests/ is INTENTIONALLY untracked since 2026-11-13 (published repo
  ships without the suite; .gitignore line 14).

## Verification
- check.sh: 1498 tests, 9 failures — ALL pre-existing on origin/main
  (test_native_display_idle swayidle argv quoting vs the apostrophe repo path).
- G0: 1304 passed / 9 failed (same pre-existing set) / 185 skipped.
- Baseline technique: `git stash push` + rerun + `git stash pop` to A/B a test
  against clean HEAD in the same checkout (worktrees fail: tests/ untracked).

## Coordination facts
- Journal now exists: /home/kimhoanglong/agent-collab/journal.md (append-only).
- Stash from the previous session's WIP preserved:
  stash@{0} "WIP async tab experiment, preserved by Agent-2 2026-11-24".
- Models all died mid-session -> finished via direct PTY control (user
  authorized); see survival-direct-control.md.
