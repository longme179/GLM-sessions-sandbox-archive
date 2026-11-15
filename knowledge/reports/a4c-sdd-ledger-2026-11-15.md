# SDD ledger — plan: /home/kimhoanglong/agent-collab/plans/2026-11-15-a4c-c2-c3-fixes.md
Preflight: worktrees a4c-clipboard/capture-fixture/suspend-native/idle-first-enable at 753dbc6, local tests/ copied, all clean. Task numbering A=1 L=2 B=3 C=4 D=5 V=6.
Ruling: G4 runs set LME_GATE_REPO to the worktree under test — the runner defaults to ~/lme-fedora-niri-qs — cost if wrong: a run could exercise main instead of the branch; every run below records its intended worktree.
Ruling (OQ-5): verified local tests stay in each worktree and back up to /tmp/opencode/a4c-fix/local-tests; shared ~/glm-work/tests-local is not overwritten pending an explicit owner choice — cost if wrong: owner must copy the set manually before the next plan.
Ruling: owner go-ahead in-session is the approval for OQ-1..OQ-6; OWNER_DECISIONS_A4C.md was not found — cost if wrong: none, conversation is the authority.
Task 1 (A): RED reproduced exactly @qml/panels/ClipboardPanel.qml[127:-1]: ReferenceError: previewClose is not defined; GREEN ClipboardInterfaceCase 1/1 OK, no ReferenceError/TypeError/Binding loop/load/assign lines; caps 172/278 exact; commit 361fa7a (2 files, +3/-3).
Task 2 (L): Step 1 REDs reproduced: worker count 9 != 1; No visible control: clipboardImage0. Demo RED superseded by PR A guard already in this worktree (plan risk table anticipates this).
Task 2: Ruling: demo case passes at L start because Task A's guard is applied — verified by the new tools()==[] assertions instead of a fresh RED — cost if wrong: the guard could be untested by a RED, but its four assertions are new and the pre-A demo run is recorded in the plan.
Task 2: Ruling: PDEATHSIG lookup uses pgrep -P only, not -f clipboard_watch.py — clipboard_watch.py execs into wl-paste, so its argv no longer contains that filename; the only child of sh is the watcher — cost if wrong: pgrep could select the wrong child, but sh has exactly one by construction.
Task 3 (B): RED reproduced: Editor state timeout + QFSFileEngine::open: No file name specified.
Task 3: Ruling: Canvas.save(filename) is broken in this Qt 6.11.2/Quickshell 0.3.2 build even in a minimal visible canvas (both overloads return false, relative/absolute/file-URL names all fail; toDataURL and grabToImage work). The plan scoped B to capture-demo.qml, but the editor's AnnotationCanvas export uses the same broken Canvas.save, so B alone cannot make the drawing case pass. I extended PR B with a separate commit replacing AnnotationCanvas export with grabToImage at Qt.size(width,height), preserving exported/exportFailed and busy. Cost if wrong: one extra product file in PR B; owner may split it, and editor export behavior needs live/G1 review.
Task 4 (C): Step 1 isolation patch applied; pre-fix test PASS 1/1. Step 2 scan: only the three suspend hits at test_laptop_features.py:149/155/159, all now patched.
Task 4: Ruling: the new module adds a fifth case (locked/activating still handshake) beyond the plan's four, and setUp hard-fails if a test reaches real secure_lock — cost if wrong: one extra local-only test; tests/ is never staged.
Task 4: Step 4 RED recorded: reachable 0 prepare calls; locked/activating 0 prepare calls; failed handshake raised no CommandError (3 fail / 2 pass).
Task 4: complete (commits 753dbc6..753dbc6, tests: bash -c 'cd /home/kimhoanglong/lme-worktrees/a4c-suspend-native && PYTHONPATH=scripts:tests python3 -m unittest -v test_a4c_suspend_native test_laptop_features.LaptopCase.test_suspend_waits_for_lock_and_reports_failure_without_sleep' → OK)
Ledger correction: task-done resolves commits in the ledger repo (main, HEAD 753dbc6), so the ranges above read 753dbc6..753dbc6. Actual branch commits: Task 1 fix/a4c-clipboard 361fa7a; Task 3 fix/a4c-capture-fixture 3daa704 + 99f1ffd; Task 4 fix/a4c-suspend-native 9e6af16. Task 2 is local-only in a4c-clipboard (no commit).
Task 5 (D): Investigation gate met — both repros RED before any fix. Probe: {'running': False, 'error': ''} != {'running': True, 'error': ''}. Restart: starts 1 != 2 with running=false and 'swayidle stopped: ' (old child exit cleared the just-installed command before the new child could spawn).
Task 5: Ruling: the plan's startCurrent omitted a publish after startChild, so after a serialized restart idleStatus.running stayed false until the next external sync while both children had started. I publish in startCurrent unconditionally (one line), which matches syncPaused's publish-after-start; cost if wrong: one extra snapshot update, no child behavior change.
Task 5: GREEN after Steps 3+5: probe case running=true/error=''; restart case starts=2/running=true/error=''; existing spawn case passes. IdleState.qml 216 <= 250; local test 89 <= 250.
Task 5: complete (commits 753dbc6..753dbc6, tests: bash -c 'cd /home/kimhoanglong/lme-worktrees/a4c-idle-first-enable && PYTHONPATH=scripts:tests python3 -m unittest -v test_a4c_idle_first_enable test_native_display_idle.DisplayIdleQmlCase.test_idle_spawns_swayidle_with_the_backend_argv' → OK)
Task 6 (V): integration branch test/a4c-c2c3-integration at ~/lme-worktrees/a4c-c2c3-integration; merged A 361fa7a, B 3daa704+99f1ffd, C 9e6af16, D 3e41c94 with --no-ff; local L + C/D modules + local architecture ratchets copied uncommitted.
Task 6: G0 PASS: 1291 passed / 0 failed / 190 skipped (known opt-in/hardware skips), 583.6s; architecture guard tests green.
Task 6: G1 BASELINE-FAIL classified, not a regression: 6 passed / 3 failed, all three test_audio_headset_ui.NativeAudioControlsCase audio-availability waits; identical names/count in five prior main-baseline G1 runs (/tmp/lme-gates.* G1.json, Nov 14). No branch product change touches audio. Plan expected 9/0/0; this is a pre-existing environment/baseline failure.
Task 6: complete (integration 07ecfdf; G4 35 passed / 0 failed / 0 skipped in 62.7s — C2 close condition; G0 1291/0/190; G1 6/3 pre-existing audio baseline; local tests + architecture ratchets uncommitted in the integration worktree).
Review triage (fresh reviewer, HEAD 07ecfdf): no Critical; 5 Important; 8 Minor. Rulings:
- Important 1 ACCEPT (Escape strands focus on the invisible Back button): plan Review Focus 1 explicitly requires Escape and Back to return to search; one-line product fix.
- Important 2 ACCEPT (focus claim untested): add functional assertions using the existing `focused`/`preview` status fields — right-click leaves search, Enter activates the focused Back and returns focus, Back click returns focus, Escape returns focus. Deviation from the reviewer's `previewFocused` field: the plan allows only capture-demo.qml as a tracked fixture change, so no native-features-demo.qml edit; cost if wrong: focus is proven by keyboard activation rather than by reading activeFocus directly.
- Important 3 ACCEPT (stale IdleState INVARIANT/GOTCHA): comments now describe probe-settled release + restart serialization.
- Important 4 ACCEPT (export may predate the latest paint): move export to `onPainted` after a deferred grab, preserving the original after-paint ordering. No deterministic RED: the race is frame-timing-only and the existing G4 drawing/pixel case is the regression test; cost if wrong: one extra frame before export.
- Important 5 ACCEPT as handoff: PR B changes qml/components/AnnotationCanvas.qml, so it is a product PR needing the owner's live editor check (Save PNG / Copy image / Extract text).
- Minor 6 DEFER (startCurrent alive-child guard): traced all interleavings of restartPending, close and the queued startCurrent; both paths compute the same argv from lastPreferences, and Quickshell ignores command replacement while running. No repro; cost if wrong: a third rapid profile change can install an inert argv until the next exit.
- Minor 7 DEFER (callLater outliving the singleton): Component.onDestruction already clears restartPending and closes; no TypeError in the 35/35 G4 teardown. Speculative; cost if wrong: a teardown log line in an abnormal exit.
- Minor 8 ACCEPT with Important 4: separate `exporting` flag keeps the concurrency guard while the async grab is in flight.
- Minor 9 DEFER (single 250 ms capture retry): G4 drawing case passed; the one-shot is the plan's prescribed retry. Latent flake recorded; cost if wrong: one retry instead of a loop on a slow first map.
- Minor 10 NO ACTION: text baseline shift is plan-prescribed and OCR still matches; fixture-only/cosmetic.
- Minor 11 ACCEPT (test-only): wait for both worker log lines instead of asserting the current count.
- Minor 12 ACCEPT (test-only): drop stale create=True from the prepare_sleep patches.
- Minor 13 ACCEPT as handoff: config/architecture.json ratchets must travel with the local test set.
Review fix A (Important 1 + 2), PR A commit 3811145:
- RED: with new focus assertions, Escape closed the preview but search stayed unfocused (and Return does not activate Back; that assertion was removed after an empirical probe).
- Mechanism (probed): Window.activeFocusItemChanged fires on Escape only after activeFocus was already dropped; immediate focusSearch, callLater, 0 ms timer, Back.clicked, button-level Escape, onReleased, declarative focus, root focus removal and root onActiveFocusChanged all failed. A 60 ms timer worked but was rejected (new timer).
- Fix: Escape sets escapeFocusPending before clearing previewImage; the existing window focus-change Connections consumes the flag and refocuses search. Probe: Escape -> focused:true, Tab -> focused:false (no focus theft). No new timer; no typed fixture field (native-features-demo.qml stays clean).
- GREEN: ClipboardInterfaceCase 1/1 OK, 8.2 s; no ReferenceError/TypeError/binding loop/load/assign errors. ClipboardPanel.qml 172/172.
Review fix B (Important 4 + 8 + 5 handoff), PR B commit (see branch log):
- exportTo now only records exportPath and requestPaint; onPainted starts finishExport after the stroke frame is painted; exporting guards re-entry through the async grab; request is cleared before grabToImage.
- GREEN: test_capture_night.NativeCaptureCase.test_drawing... 1/1 OK, 7.4 s, OCR + pixels. AnnotationCanvas.qml 77 nonblank (cap 250); capture-demo.qml 74.
- Handoff: PR B changes the shared AnnotationCanvas export path, so the owner must live-check Save PNG / Copy image / Extract text in the in-shell editor.
Review fix D (Important 3), PR D commit (see branch log):
- Rewrote the INVARIANT/GOTCHA header to describe reported exits vs restartPending respawns and the probe callback re-entry; rewrote the sync comment the reviewer flagged. IdleState.qml 218 nonblank (cap 250).
- GREEN: test_a4c_idle_first_enable 2/2 OK, 3.2 s.
Review fix C (Minor 12, test-only): dropped stale create=True from the prepare_sleep patches in tests/test_a4c_suspend_native.py (55 nonblank). GREEN: test_a4c_suspend_native 5/5 OK. No PR C product change; no product commit.
Review-fix integration (test/a4c-c2c3-integration, HEAD d27ad71):
- Merged review-fix commits: fix/a4c-clipboard 3811145, fix/a4c-capture-fixture 17b6400, fix/a4c-idle-first-enable 2730e8f; fix/a4c-suspend-native product unchanged (test-only cleanup).
- Local tests synced: test_clipboard.py 259 (Return-activation assertion removed; ratchet 259), test_clipboard_entry.py 87, test_a4c_suspend_native.py 55.
- Focused smoke: ClipboardInterfaceCase + drawing + suspend + idle = 9/9 OK, 18.5 s.
- Full G4: PASS 35/35, 0 fail, 0 skip in 63.26 s. Evidence /tmp/opencode/a4c-c2c3-g4-final, log /tmp/opencode/a4c-fix/g4-final.out.
- Caps: ClipboardPanel 172/172, ClipboardState 278/278, desktop_backend.py 1642/1642, IdleState 218 (cap 250), capture-demo 74 (cap 90), AnnotationCanvas 77 (cap 250).
Handoff state after review fixes:
- Final integration HEAD d27ad71; review package review-753dbc6..d27ad71.diff (308 lines, ignored path).
- Final local tests + architecture ratchet backed up at /tmp/opencode/a4c-fix/local-tests-final (no write to ~/glm-work/tests-local; OQ-5 still pending owner choice).
- PR branch product files only: A qml/panels/ClipboardPanel.qml + qml/services/ClipboardState.qml; B capture-demo.qml + qml/components/AnnotationCanvas.qml; C scripts/desktop_backend.py; D qml/services/IdleState.qml. No branch tracks tests/.
Final G0 at d27ad71: status completed-with-skips, returncode 0, 1291 passed / 0 failed / 190 skipped; 593.7 s. Same skip profile as the pre-review baseline (compare /tmp/opencode/a4c-g0-postpromote-202942: 1284/0/190). Evidence /tmp/opencode/a4c-c2c3-g0-final, log /tmp/opencode/a4c-fix/g0-final.out.
Gate summary after review fixes: focused 9/9; G4 35/35/0/0; G0 0 failures; local ratchets exact.
