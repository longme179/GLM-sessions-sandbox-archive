# Q5 ACTIVE STATE — read this FIRST on any new session

Last updated: 2026-11-13 (session 5: PRs #133/#134 — legs 2+3a and 3b; #130 merged, #131/#132
merged into base branches by the owner; qmldir marker bug caught and fixed)
Owner approved Q5 on 2026-11-12: "duyệt Q5 (weather, lyrics, wallpaper, file search, equalizer,
clipboard — fileOpen cũng chuyển theo entry search của Q5)". Standing rules: sub-agent prompts
in English, opencode > openrouter, deepseek-v4.1-flash-free > nemotron-3-ultra-free, remote
files under ~/glm-work/ only, owner merges PRs (never self-merge).

## Status — two stacked PRs awaiting owner review (merge in order)

- [x] **#130 leg 1 weather+lyrics** — MERGED to main (a11fefa).
- [x] **#131/#132** — merged by the owner into their stacked base branches; their content
      rides **PR #133** (qml/q5-wallpaper → main): legs 2+3a + the merge of main after #130.
      MERGE #133 FIRST.
- [x] **PR #134 leg 3b equalizer** (qml/q5-equalizer, base = qml/q5-wallpaper): EqualizerModel.js
      + the EqualizerState perform layer. Merge after #133, then retarget to main.
- [ ] **Q5 leg 4: clipboard (clipboard.py, 315 lines) — REVIEW-STOP**: propose
      Process.startDetached + PDEATHSIG (preExecCommand sets PR_SET_PDEATHSIG so the clip
      helper dies with the shell; quickshell 0.3.2 Process may kill children on destroy —
      the exact semantics need a probe) vs stays-Python until Quickshell fixes destroy
      semantics. Owner picks before coding.
- [ ] Q5 close-out + archive records + lessons.

## The qmldir lesson (session 5)

The stack merge (#133) left conflict markers in **qml/services/qmldir** — the only conflicted
file WITHOUT a known extension; the `*.py/*.json/*.qml/*.md` sweeps skipped it. Every QML
directory import then failed with quickshell's misleading "a component declaration requires
two or three arguments". Fixed in 849d682 + a contract guard sweeps the whole service
directory (test_native_state.py). Sweep rule: `grep -rln "^<<<<<<< HEAD" . --exclude-dir=.git`
with NO extension filter.

## Session-5 deliverables (context for review)

- PR #133: legs 2+3a to main + the stack merge (superset ratchets: ShellState 370, NativeState
  257, desktop_backend 1627, wl-test 279) + the qmldir fix.
- PR #134 leg 3b: EqualizerModel.js (PRESETS/normalize/stateFromDaemonLine/daemonSetArgs/
  savedView/validators) + the EqualizerState perform layer (16 eq* actions routed natively;
  staging machine exact; daemon runner = queued one-shot Process + watchdog with the
  auto-start retry; eq_state reads via FileView, writes via scripts/json_store.py — 0o600,
  fsync, atomic replace; test tone = assets/equalizer-test.wav via pw-play with pw-dump
  targeting). equalizer_actions.py DEPRECATED. Cycle edges registered (Q4 router-fan-out
  style). Ratchets: EqualizerState 442, ShellState 371, equalizer_actions 374.
- Engine-verified on the owner's machine: leg 3b 18 passed ×2; legs 1+2+3a re-verified 68
  passed on the fixed stack branch.

## Engine-test lessons (cumulative — add the rest at close-out)

- Binding-position object literals need parentheses — `property var x: ({...})` — else a
  block statement (quickshell exit 255).
- finish() from a Timer tick only (quit before the receiver connects = 15 s timeout).
- Replacement scripts over test files: assert count == 1 (the files hold two-backslash
  escapes; one-backslash searches silently no-op).
- Unquoted object keys with hyphens are syntax errors; count frame-corpus values (17 ≠ 16).
- Test helpers that normalize prefs before each call: pass flags through the helper.
- Size caps live in THREE places; cycle edges need registration in the Q4 style.
- Conflict-marker sweeps must have NO extension filter (qmldir bit us).
- Replies-ledger tests: count the ledger entries before indexing (the preset reply shifted
  the error-surface indices by one).

## Remote access

oc.sh works (credential from the 2026-11-13 handoff, stored in /home/z/my-project/.oc-auth
+ /tmp/oc_auth). Worktrees: ~/glm-work/q5leg1, q5leg2, q5leg3, q5leg3b (the full stack).
The venv: ~/glm-work/venv. Journal: /home/kimhoanglong/agent-collab/journal.md (append-only,
Agent-2 entries). qmllint exists ONLY on the remote (the sandbox has none — `grep -c` on a
missing binary prints 0, a false green).
