# Perf run `s3-a`

Tree `/home/kimhoanglong/.cache/lme-perf/rv2/p-main` at `8374e946beef`; started 2026-11-27T13:02:03; 143.4 s; ended: finished; session restored.

Latency cells are median / p95 / max in ms, with N in brackets.

## S3 - a working session

A step fails when its panel did not open, was not gone within 100 ms of the Escape key-down (state samples, 40 ms resolution), or needed a recovery. A rep fails on a failed step, a stall of 100 ms or more, a panel left open, or a workspace that was not restored.

| panel | n | input->first frame | input->open (sampled) | ESC->gone | gone->first frame | failed steps | recovered | stalls >100 / >300 | worst stall |
|---|---|---|---|---|---|---|---|---|---|
| control | 6 | – | 282.5 / 338.83 / 348.6 (n=6) | 40.1 / 60.2 / 61.2 (n=6) | {'n': 0} | 0 | 0 | 4 / 0 | 227.0 |
| activity | 9 | – | 103.5 / 127.24 / 135.8 (n=9) | – | {'n': 0} | 9 | 9 | 10 / 4 | 1417.0 |
| clipboard | 6 | – | 154.4 / 163.2 / 164.0 (n=6) | 40.65 / 56.15 / 56.7 (n=6) | {'n': 0} | 0 | 0 | 0 / 0 | 84.0 |
| overview | 6 | – | 132.7 / 170.65 / 175.0 (n=6) | 37.0 / 70.53 / 75.9 (n=4) | {'n': 0} | 2 | 2 | 3 / 3 | 3738.0 |
| launcher | 6 | – | 153.6 / 432.27 / 455.8 (n=6) | 32.95 / 79.45 / 87.7 (n=6) | {'n': 0} | 0 | 0 | 2 / 2 | 322.0 |
| notifications | 6 | – | 191.6 / 206.4 / 210.1 (n=6) | 43.25 / 53.05 / 54.2 (n=6) | {'n': 0} | 0 | 0 | 0 / 0 | 98.0 |
| power | 6 | – | 159.7 / 170.95 / 174.4 (n=6) | 45.75 / 58.75 / 62.4 (n=6) | {'n': 0} | 0 | 0 | 0 / 0 | 99.0 |
| settings | 6 | 133.87 / 1279.05 / 1654.86 (n=6) | 158.15 / 1323.5 / 1686.4 (n=6) | 90.6 / 443.4 / 529.7 (n=6) | {'n': 0} | 3 | 0 | 4 / 3 | 1753.0 |

Per rep:

| rep | load | steps | failed steps | stalls >100 / >300 | worst stall | workspace back | panel left open |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 17 | 6 | 10 / 6 | 3738.0 | the focused workspace holds no window: leaving it would remove it | False |
| 1 | 0 | 17 | 4 | 6 / 3 | 1417.0 | the focused workspace holds no window: leaving it would remove it | False |
| 2 | 0 | 17 | 4 | 8 / 4 | 2328.0 | the focused workspace holds no window: leaving it would remove it | False |

## Global (after warm-up, 1.87 min)

Exit criteria:

| criterion | measured | holds |
|---|---|---|
| S3 session: every panel opens and closes, no stall over 100 ms | 3 failed reps / 3 | NO |
| No event-loop stall over 33 ms after warm-up | 72 of 78 stalls, worst 3738.0 ms | NO |
| No frame over 2x budget (16.6 ms) | 0 frames | yes |
| p99 frame time <= 8.3 ms (settings; +0.5 ms for the 120 Hz refresh) | 13.82 ms (n=60) | NO |
| Input to first visual feedback <= 50 ms | p95 1279.05 ms, max 1654.86 ms (n=6) | NO |
| RSS <= first sample + 150 MB (shell) | +26.1 MB (max 467.6 MB) | yes |

Frame gaps per window (gaps up to 50 ms count as frames of an animation; longer ones are listed apart):

| window | frames | frame gap | > 16.6 ms | hitches 50-250 ms | pauses > 250 ms |
|---|---|---|---|---|---|
| settings | 60 | 8.0 / 12.0 / 15.0 (n=60) | 0 | 6 | 17 |

Stalls of the GUI thread (heartbeat inside the shell): 

| count | > 33 ms | > 100 ms | > 300 ms | worst | total ms | >33 per min | >100 per min |
|---|---|---|---|---|---|---|---|
| 78 | 72 | 25 | 14 | 3738.0 | 21258.0 | 38.48 | 13.36 |

What ran in the stalls (the last mark before the thread came back):

| last mark | stalls | total ms |
|---|---|---|
| - | 78 | 21258.0 |

The worst:

| at ms | ms | marks |
|---|---|---|
| 1795759382199.0 | 3738.0 | - |
| 1795759454466.0 | 2328.0 | - |
| 1795759424423.0 | 1810.0 | - |
| 1795759439200.0 | 1753.0 | - |
| 1795759365218.0 | 1529.0 | - |
| 1795759394591.0 | 1417.0 | - |
| 1795759409242.0 | 1369.0 | - |
| 1795759355109.0 | 324.0 | - |

Outside the shell:

| probe ping (GUI thread availability) | niri round trip | reference client frame gap | screen-only gaps > 50 ms | stacks taken |
|---|---|---|---|---|
| 48.77 / 71.02 / 3774.64 (n=1833) | 15.71 / 15.9 / 18.31 (n=3813) | – | 0 of 0 | 20 |

Memory (first sample after warm-up to the maximum):

| process | first MB | max MB | growth MB | samples |
|---|---|---|---|---|
| shell | 441.6 | 467.6 | 26.1 | 15256 |

Problems, skips and recoveries of the run: 12 (see summary.json).

- {"t": 1795759339052.375, "recover": "activity stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759356357.317, "recover": "activity stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759371487.343, "recover": "activity stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759382289.873, "recover": "overview stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759389471.904, "recover": "activity stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759395927.689, "recover": "activity stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759409286.252, "recover": "activity stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759422596.172, "recover": "activity stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759429657.591, "recover": "activity stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759444716.811, "recover": "activity stayed open after Escape", "how": "ipc_close"}
- {"t": 1795759454529.844, "recover": "overview stayed open after Escape", "how": "second_escape"}
- {"t": 1795759461842.069, "recover": "activity stayed open after Escape", "how": "ipc_close"}

