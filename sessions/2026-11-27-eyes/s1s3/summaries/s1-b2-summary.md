# Perf run `s1-b2`

Tree `/home/kimhoanglong/.cache/lme-perf/rv2/p-head` at `33c687c48678`; started 2026-11-27T12:24:17; 100.1 s; ended: finished; session restored.

Latency cells are median / p95 / max in ms, with N in brackets.

## S1 - Control Center tabs

A rep fails when the GUI thread was unavailable for 100 ms or more inside it (heartbeat), when the last tab clicked did not end shown, built and opaque, or when Escape did not close the panel.

| variant | reps | clicks | final tab ok | failed reps | which | last click->settled | freeze reps | stalls >100 / >300 | worst stall | ESC->gone | ESC failures |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ordered | 3 | 18 | 3/3 | 2 | [0, 1] | 395.14 / 397.95 / 398.26 (n=3) | 2/3 | 6 / 2 | 1768.0 | 20.67 / 23.68 / 24.01 (n=3) | 0 |
| random | 3 | 36 | 3/3 | 2 | [0, 2] | 390.24 / 396.39 / 397.07 (n=3) | 2/3 | 2 / 2 | 3088.0 | 20.27 / 21.83 / 22.0 (n=3) | 0 |

Per tab (variant `ordered`):

| tab | click->built/present | click->settled | click->first frame |
|---|---|---|---|
| agenda | 8.93 / 9.2 / 9.23 (n=3) | 386.23 / 391.35 / 391.92 (n=3) | – |
| audio | 11.16 / 12.08 / 12.18 (n=3) | 385.18 / 390.56 / 391.16 (n=3) | – |
| controls | 9.45 / 9.48 / 9.48 (n=2) | 397.48 / 415.43 / 417.42 (n=3) | – |
| devices | 9.82 / 11.87 / 12.1 (n=3) | 387.1 / 394.05 / 394.82 (n=3) | – |
| notifications | 14.14 / 132.89 / 146.09 (n=3) | 518.09 / 655.46 / 670.72 (n=3) | – |
| system | 9.26 / 9.38 / 9.39 (n=3) | 395.13 / 397.95 / 398.26 (n=3) | – |

## Global (after warm-up, 1.21 min)

Exit criteria:

| criterion | measured | holds |
|---|---|---|
| S1 Control Center: no freeze, last tab shown, Escape closes it | 4 failed reps / 6 | NO |
| No event-loop stall over 33 ms after warm-up | 13 of 13 stalls, worst 3088.0 ms | NO |
| No frame over 2x budget (16.6 ms) | 0 frames | yes |
| Input to first visual feedback <= 50 ms | p95 None ms, max None ms (n=0) | NO |
| RSS <= first sample + 150 MB (shell) | +40.3 MB (max 473.8 MB) | yes |

Frame gaps per window (gaps up to 50 ms count as frames of an animation; longer ones are listed apart):

| window | frames | frame gap | > 16.6 ms | hitches 50-250 ms | pauses > 250 ms |
|---|---|---|---|---|---|

Stalls of the GUI thread (heartbeat inside the shell): 

| count | > 33 ms | > 100 ms | > 300 ms | worst | total ms | >33 per min | >100 per min |
|---|---|---|---|---|---|---|---|
| 13 | 13 | 12 | 6 | 3088.0 | 11792.0 | 10.7 | 9.88 |

What ran in the stalls (the last mark before the thread came back):

| last mark | stalls | total ms |
|---|---|---|
| - | 13 | 11792.0 |

The worst:

| at ms | ms | marks |
|---|---|---|
| 1795757130542.0 | 3088.0 | - |
| 1795757085900.0 | 2758.0 | - |
| 1795757100543.0 | 1768.0 | - |
| 1795757143588.0 | 1425.0 | - |
| 1795757098771.0 | 919.0 | - |
| 1795757147102.0 | 315.0 | - |
| 1795757112872.0 | 292.0 | - |
| 1795757105062.0 | 280.0 | - |

Outside the shell:

| probe ping (GUI thread availability) | niri round trip | reference client frame gap | screen-only gaps > 50 ms | stacks taken |
|---|---|---|---|---|
| 48.08 / 56.01 / 3112.12 (n=1235) | 15.71 / 15.93 / 32.04 (n=2413) | – | 0 of 0 | 11 |

Memory (first sample after warm-up to the maximum):

| process | first MB | max MB | growth MB | samples |
|---|---|---|---|---|
| shell | 433.5 | 473.8 | 40.3 | 9655 |

