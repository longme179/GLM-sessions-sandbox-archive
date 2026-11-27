# Perf run `s3-b2`

Tree `/home/kimhoanglong/.cache/lme-perf/rv2/p-head` at `33c687c48678`; started 2026-11-27T12:33:17; 111.8 s; ended: finished; session restored.

Latency cells are median / p95 / max in ms, with N in brackets.

## S3 - a working session

A step fails when its panel did not open, was not gone within 100 ms of the Escape key-down (state samples, 40 ms resolution), or needed a recovery. A rep fails on a failed step, a stall of 100 ms or more, a panel left open, or a workspace that was not restored.

| panel | n | input->first frame | input->open (sampled) | ESC->gone | gone->first frame | failed steps | recovered | stalls >100 / >300 | worst stall |
|---|---|---|---|---|---|---|---|---|---|
| control | 6 | – | 304.0 / 350.77 / 359.5 (n=6) | 42.05 / 58.83 / 61.9 (n=6) | {'n': 0} | 0 | 0 | 4 / 0 | 223.0 |
| activity | 9 | – | 106.7 / 126.38 / 130.5 (n=9) | 16.7 / 285.48 / 451.6 (n=9) | {'n': 0} | 1 | 0 | 6 / 1 | 1058.0 |
| clipboard | 6 | – | 143.2 / 170.48 / 176.8 (n=6) | 38.05 / 51.77 / 52.6 (n=6) | {'n': 0} | 0 | 0 | 0 / 0 | 78.0 |
| overview | 6 | – | 124.8 / 2224.95 / 2914.1 (n=6) | 36.75 / 123.02 / 149.7 (n=6) | {'n': 0} | 1 | 0 | 3 / 3 | 2368.0 |
| launcher | 6 | – | 155.15 / 344.27 / 399.4 (n=6) | 48.5 / 276.8 / 325.5 (n=5) | {'n': 0} | 2 | 1 | 4 / 3 | 2552.0 |
| notifications | 6 | – | 181.15 / 200.97 / 202.1 (n=6) | 46.35 / 974.42 / 1283.1 (n=6) | {'n': 0} | 1 | 0 | 3 / 1 | 1752.0 |
| power | 6 | – | 155.15 / 171.05 / 173.9 (n=6) | 30.8 / 38.16 / 38.6 (n=5) | {'n': 0} | 1 | 1 | 1 / 1 | 2345.0 |
| settings | 6 | 123.21 / 160.75 / 166.86 (n=6) | 151.65 / 214.4 / 233.4 (n=6) | 235.8 / 459.07 / 487.7 (n=6) | {'n': 0} | 4 | 0 | 1 / 1 | 388.0 |

Per rep:

| rep | load | steps | failed steps | stalls >100 / >300 | worst stall | workspace back | panel left open |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 17 | 4 | 8 / 4 | 1058.0 | the focused workspace holds no window: leaving it would remove it | False |
| 1 | 0 | 17 | 3 | 8 / 3 | 2368.0 | the focused workspace holds no window: leaving it would remove it | False |
| 2 | 0 | 17 | 3 | 8 / 4 | 2552.0 | the focused workspace holds no window: leaving it would remove it | False |

## Global (after warm-up, 1.41 min)

Exit criteria:

| criterion | measured | holds |
|---|---|---|
| S3 session: every panel opens and closes, no stall over 100 ms | 3 failed reps / 3 | NO |
| No event-loop stall over 33 ms after warm-up | 72 of 74 stalls, worst 2552.0 ms | NO |
| No frame over 2x budget (16.6 ms) | 2 frames | NO |
| p99 frame time <= 8.3 ms (settings; +0.5 ms for the 120 Hz refresh) | 14.8 ms (n=156) | NO |
| Input to first visual feedback <= 50 ms | p95 160.75 ms, max 166.86 ms (n=6) | NO |
| RSS <= first sample + 150 MB (shell) | +47.7 MB (max 472.6 MB) | yes |

Frame gaps per window (gaps up to 50 ms count as frames of an animation; longer ones are listed apart):

| window | frames | frame gap | > 16.6 ms | hitches 50-250 ms | pauses > 250 ms |
|---|---|---|---|---|---|
| settings | 156 | 8.0 / 9.0 / 17.0 (n=156) | 2 | 7 | 14 |

Stalls of the GUI thread (heartbeat inside the shell): 

| count | > 33 ms | > 100 ms | > 300 ms | worst | total ms | >33 per min | >100 per min |
|---|---|---|---|---|---|---|---|
| 74 | 72 | 25 | 11 | 2552.0 | 18436.0 | 51.16 | 17.77 |

What ran in the stalls (the last mark before the thread came back):

| last mark | stalls | total ms |
|---|---|---|
| - | 74 | 18436.0 |

The worst:

| at ms | ms | marks |
|---|---|---|
| 1795757683422.0 | 2552.0 | - |
| 1795757653770.0 | 2368.0 | - |
| 1795757697930.0 | 2345.0 | - |
| 1795757667913.0 | 1752.0 | - |
| 1795757623557.0 | 1058.0 | - |
| 1795757637711.0 | 1052.0 | - |
| 1795757654232.0 | 458.0 | - |
| 1795757687103.0 | 388.0 | - |

Outside the shell:

| probe ping (GUI thread availability) | niri round trip | reference client frame gap | screen-only gaps > 50 ms | stacks taken |
|---|---|---|---|---|
| 48.53 / 79.22 / 2572.88 (n=1331) | 15.72 / 15.91 / 31.77 (n=2732) | – | 0 of 0 | 19 |

Memory (first sample after warm-up to the maximum):

| process | first MB | max MB | growth MB | samples |
|---|---|---|---|---|
| shell | 424.9 | 472.6 | 47.7 | 10927 |

Problems, skips and recoveries of the run: 2 (see summary.json).

- {"t": 1795757683586.299, "recover": "launcher stayed open after Escape", "how": "second_escape"}
- {"t": 1795757697983.234, "recover": "power stayed open after Escape", "how": "second_escape"}

