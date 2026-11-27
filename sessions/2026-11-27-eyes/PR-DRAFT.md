# PR draft — `perf/responsive-v2` → `main`

Draft for the owner to review and paste. Written in English because the repository's commits,
README and code comments are in English. Head of the branch when this was written: `a7df45c`
(49 commits over `main`, 44 of them touching `scripts/perf`). Outside `scripts/perf` the branch
changes `shell.qml`, `qml/components/PageHost.qml`, `qml/services/Heartbeat.qml`,
`qml/services/qmldir` and `config/architecture.json`; `AGENTS.md` is unchanged against `main`.

## Title

`fix(shell): Escape closes the activity island; perf harness and GUI-thread watchdog`

## Summary

**One behavioural change, in `shell.qml`** (commit `33b204d`): the panel stage no longer takes
keyboard focus while the activity island is the open surface. Before, `onPanelOpenChanged`
called `forceActiveFocus()` on the panel stage as soon as `panelOpen` was set. That stage is
hidden while the island is shown (`shown: panelOpen && !activityOpen`), and focusing a hidden
item clears the window's `activeFocusItem`, so no `Keys` handler ever saw Escape: the island
opened and did not close on Escape.

**Everything else is measurement tooling**, off unless it is asked for:

- `qml/services/Heartbeat.qml` (+ `qmldir`, build marks in `qml/components/PageHost.qml`, commit
  `7fc1df9`): a GUI-thread stall watchdog. A 4 ms timer can only fire when the thread is free, so
  the gap between two beats is the time the thread was unavailable. It runs only with
  `LME_SHELL_WATCHDOG=1`; without it the timer never starts and `mark()` returns at once.
- `scripts/perf/**`: the harness that produced the numbers below — real input over one uinput
  device pair, an instrumented stand-in shell swapped in and restored with a dead-man timer, a
  probe that only watches, an offline model with a self-test. See `scripts/perf/README.md`.
- `config/architecture.json`: lists the harness files. The file's mode is back to 644 (`29c6f81`);
  the two eyes files are listed (`a7df45c`).
- `AGENTS.md`: no net change against `main`. The temporary real-session exception (`4469385`) is
  reverted in `5fc777b`, as its own message asked.

## Evidence for the fix

S4 of the harness: open the island, press Escape 5–400 ms later, assert it is gone within 100 ms.

| tree | runs (2026-11-26, host time +07) | result |
|---|---|---|
| without the fix, `db2facb95870` | `183022-s4-full-a`, `184515-s4-panel-warm`, `184704-s4-one-panel` | 12 failures / 12 cycles |
| with the fix, `9377fbcfd476` | `185358-s4-fixed-b` | 0 failures / 4 cycles |
| with the fix, `249420b70958` | `201626-s4-prior-meas-b`: Escape 60, 100, 150, 250, 400 ms after the open, a Control Center opened before the island | 0 failures / 20 cycles |

In the longer run `185606-s4-n10-b` (41 cycles) 38 closed; the 3 failures are classified
`frozen` by the harness (the GUI thread was stalled), not a lost Escape.

Same harness build on both trees on 2026-11-27 (probe `6fc853ea329a`), the "activity" steps of
S3 (3 repetitions of 3 steps). The `main` tree carried the watchdog commit `7fc1df9` on top so
that the probe could take the same marks on both sides; the watchdog is inert without
`LME_SHELL_WATCHDOG=1`.

| tree | closed by the first Escape | how long | needed the harness to close it over IPC |
|---|---|---|---|
| `main` at `8374e94` | 0 of 9 | – | 9 of 9 |
| branch at `33c687c` | 9 of 9 | median 16.7 ms, max 451.6 ms | 0 |

On `main` the same happened once more in the warm-up of each of the three runs of that day (S3,
S1, S1 fast): the harness logged "activity stayed open after Escape" and closed it over IPC. In
all that is 12 times on `main`; it did not happen in these runs on the branch.

## What this PR does not fix (measured, same harness on both trees, 2026-11-27)

Each side ran 3 repetitions per variant in one session. That is below the harness rule for
keeping a change (N >= 10 per side): these numbers show where the branch stands, they are not a
verdict. Full tables are kept outside the repository, in the campaign folder:
`AB-S1S3-COMPARE.txt` and `AB-S2-COMPARE.txt`.

**S1, Control Center tabs** — unchanged by the branch.

- Every click reached its tab on both sides: click → tab mark 9–16 ms (medians per tab), Escape →
  gone 20–24 ms. Click → page settled is 385–403 ms for every tab except `notifications` on the
  branch (518 ms median, up to 671 ms). The 54 screenshots per side all show the click point in
  the middle of a 287–288 × 40 px tab button.
- The GUI thread still stalls on both sides while a page is built for the first time. Over the 9
  repetitions (ordered, random, fast): `main` 13 stalls over 100 ms (10 over 300 ms, worst
  2215 ms), branch 9 (5 over 300 ms, worst 3088 ms). In the ordered pass on `main` the `devices`
  tab took up to 1465 ms and `agenda` 730 ms to settle; on the branch `notifications` up to 671 ms.

**S2, Settings pages** — unchanged by the branch. One click per page, 18 pages × 3 repetitions on
each side: a click that never navigates happened 16 times out of 54 on `main` and 17 out of 54 on
the branch; 16 (repetition, page) pairs are the same on both, the one extra on the branch is
`about` in the first repetition.

**S3, mixed panels** — latencies are the same on both sides; the long tails differ in where they
land, not in size.

- Open: Control Center 283 ms (`main`) / 304 ms (branch) median; the other panels 104–192 ms
  median on both sides.
- Escape → gone: 17–49 ms median for the shell overlays on both sides, where they closed.
  Settings, which is its own window: 91 ms median on `main`, 236 ms on the branch (max
  530 / 488 ms).
- Tails on `main`: `overview` stayed open twice (one second Escape, one IPC close); a stall of
  3738 ms inside the recovery of a panel that did not close; `settings` once 1686 ms to open.
- Tails on the branch: `overview` once 2914 ms to open, `notifications` once 1283 ms to close,
  and once each `launcher` and `power` needed a second Escape.
- The workspace step of S3 was skipped on both sides: the focused workspace held no window, and
  leaving it would have removed it.

## Checks

- `bash scripts/check.sh` on `a7df45c`: exit code 0. Architecture checks pass (dependency, cycle,
  source size, language mix), demo backend snapshot valid, backend tests and Bash syntax checks
  pass. The unit tests are skipped by the script itself (no `tests/` directory).
- `python3 scripts/perf/selftest.py`: 9 of 9 cases on the model (host, 2026-11-27). Case `ghost`
  had been red: the harness waits about 400 ms for a nav entry to settle before each click of an
  S2 burst, but the model ended a burst 150 ms after a click. Fixed in `aa77a09`; scenarios,
  detectors and analyzer are unchanged.

## Reviewing

- The behavioural change is one condition in `shell.qml` (`33b204d`); the same commit also
  extends the probe patch so the harness can observe it.
- If a shell-only PR is preferred: `33b204d` and `7fc1df9` are the two commits outside
  `scripts/perf` that change the shell; everything else is the harness.
- The harness needs an instrumented stand-in shell in a real session to measure; nothing in it
  runs unless `scripts/perf/run.py` is started by hand.
