# Q5 ACTIVE STATE — read this FIRST on any new session

Last updated: 2026-11-13 late (session 6: leg 4 clipboard delivered as PR #137 — Option A
approved by the owner; tests policy PR #136; leg 3b delivered as PR #135 after the
#134-into-branch merge trap)
Owner approved Q5 on 2026-11-12: "duyệt Q5 (weather, lyrics, wallpaper, file search,
equalizer, clipboard — fileOpen cũng chuyển theo entry search của Q5)". Standing rules:
sub-agent prompts in English, opencode > openrouter, deepseek-v4.1-flash-free >
nemotron-3-ultra-free, remote files under ~/glm-work/ only, owner merges PRs (never
self-merge).

## NEW STANDING POLICY (owner, 2026-11-13): tests stay local

`tests/` is UNTRACKED and gitignored (PR #136): never push test files; the suite runs
from the local working set (sandbox: /home/z/my-project/repos/lme-fedora-niri-qs/tests,
remote: ~/glm-work/tests-local — restore into a worktree with `cp -r
~/glm-work/tests-local/. <worktree>/tests/` after creating it, since fresh branches carry
no tests). check.sh skips discovery where tests/ is absent. New tests are written to the
local tests/ dir only and copied to the remote worktree via base64 for verification.

## Status — three stacked PRs awaiting owner review (merge in order)

- [x] #130 leg 1 weather+lyrics — merged to main.
- [x] #133 legs 2+3a — merged to main (9ed7f43).
- [x] **PR #135**: leg 3b equalizer → main (the #134 squash landed on qml/q5-wallpaper
      after #133; this carries it the last hop). MERGE FIRST.
- [x] **PR #136**: tests-local policy (base qml/q5-wallpaper, retargets to main after
      #135). Then the owner's main checkout loses tests/ on pull — restore with
      `cp -r ~/glm-work/tests-local/. ~/lme-fedora-niri-qs/tests/`.
- [x] **PR #137**: Q5 leg 4 clipboard (base policy/local-tests-only → retargets after
      #136). Engine-verified on the owner's machine: 33 passed ×2 + the full suite run.
      The owner already ran the new code live (both wl-paste watchers up with the exact
      clipboard_watch.py argv from their main checkout).
- [ ] Q5 close-out (after the owner merges #135/#136/#137): the final summary, archive
      records, and the Q6 proposal review-stop.

## Session-6 decisions and evidence (context for review)

- **The quickshell 0.3.2 kill-semantics probe** (live, on the owner's machine): normal
  exit SIGKILLs direct Process children (no orphans); a `kill -9` crash leaves a plain
  child ORPHANED, while the idle_control-style PR_SET_PDEATHSIG wrapper (armed against
  the shell pid, `--parent` is only the early-death guard) dies clean on the kernel
  SIGTERM. startDetached does NOT exist in 0.3.2 (documented deviation from the
  option-A sketch; the owner approved the native direction, not the exact API).
- **Leg 4 architecture**: the JSON-lines serve daemon retired (−123 lines);
  ClipboardState.qml runs one-shot clipboard.py subcommands (--state/--search/--copy/
  --pin/--delete/--clear/--pause/--configure, one JSON line per run, messages identical);
  scripts/clipboard_watch.py = flock + PR_SET_PDEATHSIG + exec wl-paste --watch; the
  panel gains one line (onVisibleChanged → monitoring gates a 2 s revision poll).
- **The bug the test caught**: the flock fd must be os.set_inheritable — Python's
  close-on-exec default drops the lock at execvp, re-enabling duplicate capture.
- **Two test-harness traps this session**: (1) bash `sh -c 'single command'` EXECs
  instead of forking, so `--parent $$` equals the child's own pid and the getppid guard
  fires — spawn with `& wait` to force a real fork; (2) a fake argv matcher must use
  argv.includes (—search takes two trailing args, positional probes misfire).

## Cumulative engine-test lessons

- Binding-position object literals need parentheses — `property var x: ({...})`.
- finish() from a Timer tick only; count ledger entries before indexing them.
- Replacement scripts over test files: assert count == 1 (two-backslash escapes).
- Unquoted object keys with hyphens are syntax errors; count frame-corpus values.
- Size caps live in THREE places; cycle edges need registration in the Q4 style.
- Conflict-marker sweeps must have NO extension filter (qmldir bit us).
- bash sh -c exec-optimization breaks $$ parent tests — use `& wait`.
- Fake transport matchers: argv.includes, not positional probes.
- Test-first discipline catches real bugs: the flock fd close-on-exec (leg 4).

## Remote access

oc.sh works (credential in /home/z/my-project/.oc-auth → /tmp/oc_auth). Worktrees:
~/glm-work/q5leg1..q5leg4 (q5leg4 = the full stack + the local test set), venv
~/glm-work/venv, tests backup ~/glm-work/tests-local. Journal:
/home/kimhoanglong/agent-collab/journal.md (append-only, Agent-2 entries). qmllint only
on the remote. base64 payloads through oc.sh need LOCAL expansion (single-quoted "$B64"
arrives empty — the round-1 probe ran an empty fixture for two rounds before the
"File is empty" error gave it away).
