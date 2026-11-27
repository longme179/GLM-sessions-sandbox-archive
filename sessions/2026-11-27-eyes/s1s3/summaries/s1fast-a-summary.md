# Perf run `s1fast-a`

Tree `/home/kimhoanglong/.cache/lme-perf/rv2/p-main` at `8374e946beef`; started 2026-11-27T13:04:33; 55.1 s; ended: finished; session restored.

Latency cells are median / p95 / max in ms, with N in brackets.

## S1 - Control Center tabs

A rep fails when the GUI thread was unavailable for 100 ms or more inside it (heartbeat), when the last tab clicked did not end shown, built and opaque, or when Escape did not close the panel.

| variant | reps | clicks | final tab ok | failed reps | which | last click->settled | freeze reps | stalls >100 / >300 | worst stall | ESC->gone | ESC failures |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fast | 3 | 1062 | 3/3 | 2 | [1, 2] | 480.08 / 484.72 / 485.23 (n=3) | 2/3 | 4 / 1 | 813.0 | 20.96 / 23.94 / 24.27 (n=3) | 0 |

## Global (after warm-up, 0.39 min)

Exit criteria:

| criterion | measured | holds |
|---|---|---|
| S1 Control Center: no freeze, last tab shown, Escape closes it | 2 failed reps / 3 | NO |
| No event-loop stall over 33 ms after warm-up | 9 of 10 stalls, worst 813.0 ms | NO |
| No frame over 2x budget (16.6 ms) | 0 frames | yes |
| Input to first visual feedback <= 50 ms | p95 None ms, max None ms (n=0) | NO |
| RSS <= first sample + 150 MB (shell) | +5.1 MB (max 452.2 MB) | yes |

Frame gaps per window (gaps up to 50 ms count as frames of an animation; longer ones are listed apart):

| window | frames | frame gap | > 16.6 ms | hitches 50-250 ms | pauses > 250 ms |
|---|---|---|---|---|---|

Stalls of the GUI thread (heartbeat inside the shell): 

| count | > 33 ms | > 100 ms | > 300 ms | worst | total ms | >33 per min | >100 per min |
|---|---|---|---|---|---|---|---|
| 10 | 9 | 6 | 1 | 813.0 | 2332.0 | 23.34 | 15.56 |

What ran in the stalls (the last mark before the thread came back):

| last mark | stalls | total ms |
|---|---|---|
| - | 10 | 2332.0 |

The worst:

| at ms | ms | marks |
|---|---|---|
| 1795759514997.0 | 813.0 | - |
| 1795759517073.0 | 294.0 | - |
| 1795759523073.0 | 283.0 | - |
| 1795759505062.0 | 277.0 | - |
| 1795759515266.0 | 265.0 | - |
| 1795759502710.0 | 219.0 | - |
| 1795759515331.0 | 61.0 | - |
| 1795759523129.0 | 52.0 | - |

Outside the shell:

| probe ping (GUI thread availability) | niri round trip | reference client frame gap | screen-only gaps > 50 ms | stacks taken |
|---|---|---|---|---|
| 50.31 / 87.58 / 1170.64 (n=352) | 15.72 / 15.93 / 16.29 (n=723) | – | 0 of 0 | 5 |

Memory (first sample after warm-up to the maximum):

| process | first MB | max MB | growth MB | samples |
|---|---|---|---|---|
| shell | 447.1 | 452.2 | 5.1 | 2893 |

Problems, skips and recoveries of the run: 1 (see summary.json).

- {"t": 1795759490057.437, "recover": "activity stayed open after Escape", "how": "ipc_close"}

