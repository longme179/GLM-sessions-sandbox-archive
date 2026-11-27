# Perf run `s1fast-b2`

Tree `/home/kimhoanglong/.cache/lme-perf/rv2/p-head` at `33c687c48678`; started 2026-11-27T12:35:16; 54.9 s; ended: finished; session restored.

Latency cells are median / p95 / max in ms, with N in brackets.

## S1 - Control Center tabs

A rep fails when the GUI thread was unavailable for 100 ms or more inside it (heartbeat), when the last tab clicked did not end shown, built and opaque, or when Escape did not close the panel.

| variant | reps | clicks | final tab ok | failed reps | which | last click->settled | freeze reps | stalls >100 / >300 | worst stall | ESC->gone | ESC failures |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fast | 3 | 1062 | 3/3 | 1 | [0] | 425.44 / 442.8 / 444.73 (n=3) | 1/3 | 1 / 0 | 279.0 | 21.74 / 22.86 / 22.98 (n=3) | 0 |

## Global (after warm-up, 0.45 min)

Exit criteria:

| criterion | measured | holds |
|---|---|---|
| S1 Control Center: no freeze, last tab shown, Escape closes it | 1 failed reps / 3 | NO |
| No event-loop stall over 33 ms after warm-up | 10 of 13 stalls, worst 2324.0 ms | NO |
| No frame over 2x budget (16.6 ms) | 0 frames | yes |
| Input to first visual feedback <= 50 ms | p95 None ms, max None ms (n=0) | NO |
| RSS <= first sample + 150 MB (shell) | +34.0 MB (max 470.6 MB) | yes |

Frame gaps per window (gaps up to 50 ms count as frames of an animation; longer ones are listed apart):

| window | frames | frame gap | > 16.6 ms | hitches 50-250 ms | pauses > 250 ms |
|---|---|---|---|---|---|

Stalls of the GUI thread (heartbeat inside the shell): 

| count | > 33 ms | > 100 ms | > 300 ms | worst | total ms | >33 per min | >100 per min |
|---|---|---|---|---|---|---|---|
| 13 | 10 | 5 | 2 | 2324.0 | 4415.0 | 22.12 | 11.06 |

What ran in the stalls (the last mark before the thread came back):

| last mark | stalls | total ms |
|---|---|---|
| - | 13 | 4415.0 |

The worst:

| at ms | ms | marks |
|---|---|---|
| 1795757744029.0 | 2324.0 | - |
| 1795757757459.0 | 958.0 | - |
| 1795757747063.0 | 279.0 | - |
| 1795757759053.0 | 268.0 | - |
| 1795757740286.0 | 222.0 | - |
| 1795757747146.0 | 79.0 | - |
| 1795757740613.0 | 54.0 | - |
| 1795757740341.0 | 51.0 | - |

Outside the shell:

| probe ping (GUI thread availability) | niri round trip | reference client frame gap | screen-only gaps > 50 ms | stacks taken |
|---|---|---|---|---|
| 49.56 / 83.93 / 2365.98 (n=398) | 15.72 / 15.93 / 16.31 (n=842) | – | 0 of 0 | 5 |

Memory (first sample after warm-up to the maximum):

| process | first MB | max MB | growth MB | samples |
|---|---|---|---|---|
| shell | 436.6 | 470.6 | 34.0 | 3371 |

