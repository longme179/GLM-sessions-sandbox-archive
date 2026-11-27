# Perf run `s1-a`

Tree `/home/kimhoanglong/.cache/lme-perf/rv2/p-main` at `8374e946beef`; started 2026-11-27T13:00:13; 103.1 s; ended: finished; session restored.

Latency cells are median / p95 / max in ms, with N in brackets.

## S1 - Control Center tabs

A rep fails when the GUI thread was unavailable for 100 ms or more inside it (heartbeat), when the last tab clicked did not end shown, built and opaque, or when Escape did not close the panel.

| variant | reps | clicks | final tab ok | failed reps | which | last click->settled | freeze reps | stalls >100 / >300 | worst stall | ESC->gone | ESC failures |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ordered | 3 | 18 | 3/3 | 2 | [0, 1] | 391.47 / 408.53 / 410.43 (n=3) | 2/3 | 5 / 5 | 1419.0 | 21.99 / 23.65 / 23.83 (n=3) | 0 |
| random | 3 | 36 | 3/3 | 3 | [0, 1, 2] | 395.19 / 474.63 / 483.46 (n=3) | 3/3 | 4 / 4 | 2215.0 | 19.81 / 21.54 / 21.73 (n=3) | 0 |

Per tab (variant `ordered`):

| tab | click->built/present | click->settled | click->first frame |
|---|---|---|---|
| agenda | 11.59 / 11.99 / 12.04 (n=3) | 395.03 / 696.54 / 730.04 (n=3) | – |
| audio | 9.19 / 11.46 / 11.71 (n=3) | 391.71 / 393.94 / 394.19 (n=3) | – |
| controls | 11.14 / 11.52 / 11.56 (n=2) | 392.73 / 401.58 / 402.56 (n=3) | – |
| devices | 9.25 / 12.11 / 12.43 (n=3) | 403.25 / 1358.94 / 1465.13 (n=3) | – |
| notifications | 15.11 / 16.32 / 16.45 (n=3) | 393.45 / 400.65 / 401.45 (n=3) | – |
| system | 16.08 / 17.29 / 17.43 (n=3) | 391.47 / 408.53 / 410.43 (n=3) | – |

## Global (after warm-up, 1.2 min)

Exit criteria:

| criterion | measured | holds |
|---|---|---|
| S1 Control Center: no freeze, last tab shown, Escape closes it | 5 failed reps / 6 | NO |
| No event-loop stall over 33 ms after warm-up | 13 of 14 stalls, worst 2215.0 ms | NO |
| No frame over 2x budget (16.6 ms) | 0 frames | yes |
| Input to first visual feedback <= 50 ms | p95 None ms, max None ms (n=0) | NO |
| RSS <= first sample + 150 MB (shell) | +34.2 MB (max 471.2 MB) | yes |

Frame gaps per window (gaps up to 50 ms count as frames of an animation; longer ones are listed apart):

| window | frames | frame gap | > 16.6 ms | hitches 50-250 ms | pauses > 250 ms |
|---|---|---|---|---|---|

Stalls of the GUI thread (heartbeat inside the shell): 

| count | > 33 ms | > 100 ms | > 300 ms | worst | total ms | >33 per min | >100 per min |
|---|---|---|---|---|---|---|---|
| 14 | 13 | 11 | 11 | 2215.0 | 8027.0 | 10.84 | 9.17 |

What ran in the stalls (the last mark before the thread came back):

| last mark | stalls | total ms |
|---|---|---|
| - | 14 | 8027.0 |

The worst:

| at ms | ms | marks |
|---|---|---|
| 1795759300469.0 | 2215.0 | - |
| 1795759255508.0 | 1419.0 | - |
| 1795759284555.0 | 1039.0 | - |
| 1795759269448.0 | 625.0 | - |
| 1795759241305.0 | 536.0 | - |
| 1795759269894.0 | 442.0 | - |
| 1795759259112.0 | 334.0 | - |
| 1795759289109.0 | 328.0 | - |

Outside the shell:

| probe ping (GUI thread availability) | niri round trip | reference client frame gap | screen-only gaps > 50 ms | stacks taken |
|---|---|---|---|---|
| 47.03 / 54.98 / 2249.54 (n=1326) | 15.72 / 15.94 / 31.92 (n=2406) | – | 0 of 0 | 10 |

Memory (first sample after warm-up to the maximum):

| process | first MB | max MB | growth MB | samples |
|---|---|---|---|---|
| shell | 437.1 | 471.2 | 34.2 | 9625 |

Problems, skips and recoveries of the run: 1 (see summary.json).

- {"t": 1795759230044.523, "recover": "activity stayed open after Escape", "how": "ipc_close"}

