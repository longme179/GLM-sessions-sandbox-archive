# Session 2026-11-16 (early AM +07) — iNiR → LME port analysis (agent-2 as orchestrator)

Mission: rigorous read-only report on what LME Shell should port from iNiR, written to
the owner's `~/agent-collab/reports/inir-vs-lme/`. Analysis only; nothing modified.

## What happened
- Bootstrap: archive repo pulled (NOT empty — followed existing structure + FUTURE-SELF),
  auth bridge rebuilt per tools/README contract, opencode gateway v2.2.6 alive, agent-1
  = NEW session `ses_e1f8cc42dffeTa7WCBaXWnPy7S` (baidu/ernie-5.5-flash-preview:free,
  "dev-lme-shell-continue").
- T01 (agent-1): workspace dirs + shallow clones + meta.json — DONE first try.
  Pins: **iNiR @ 2836543 (v3.1.1)**, **LME @ 7bc362d**. T02 (agent-1): machine facts —
  hybrid GPU (RTX 4050 + AMD Rembrandt iGPU), quickshell 0.3.2, niri 26.04; missing
  satty/cliphist/ydotool/mpv.
- Agent-2: local clones at the same pins; read LME framing docs (INIR_PORT, STATE,
  ROADMAP, FEATURE_PORTS, OPTIMIZATION/NEXT_OPTIMIZATION, Q6 proposal) and iNiR README/
  CHANGELOG/docs; found the prior comparison (reports/2026-11-13-inir-comparison.md) and
  that its Tier A items A1/A2/A4/A7/A12 + lock phases 1-3 had since MERGED (git log
  b3deed1..HEAD, 73 commits). 6 Explore subagents → per-area inventories; 11 key
  citations spot-verified locally.
- Wrote 00-06 + README + meta + machine-facts + tasks/ + orchestration log; delivered
  byte-exact (md5) to the owner's machine; T03 (agent-1 verification of P0/P1 line
  ranges) dispatched. Archive commit follows this note.

## Key durable facts (see knowledge/inir-lme-port-map.md for the full map)
- iNiR v3.x architecture: base repo + inir-hub plugins (UI families!) + qs-rs Rust
  runtime + inir-accel + inir-cli, all prebuilt. NO patches/ dir anymore. Mission
  briefs describing "patches/quickshell" are stale.
- The top LME gaps: alt-tab switcher (absent), in-shell frozen-frame region selector
  (LME's own recorded port candidate), niri event batching/membership/stable-IDs,
  update verify/auto-rollback, Overview thumbnails (cached-stills variant is portable;
  live streams are qs-rs-only).
- LME is AGPL-3.0; GPL-3.0 §13 adoption practice is established in THIRD_PARTY.md.

## What worked / what to do differently
- Worked: agent-2-does-analysis + agent-1-does-machine split; oc2.py dispatch-with-wait;
  background dispatches during local work; byte-exact puts; prompt template above
  (3/3 agent-1 tasks done first try).
- Differently: pull the journal tail + prior reports BEFORE writing prompts (I did, and
  it saved re-recommending merged work); check `git log <prior-baseline>..HEAD` early —
  the delta IS the "already done" list.
- Flash-agent limits observed: none this session when tasks were literal; keep it that way.
