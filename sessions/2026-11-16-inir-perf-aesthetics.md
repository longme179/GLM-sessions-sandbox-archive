# Session 2026-11-16 (part 2) — perf & aesthetics comparison (owner redirect)

Owner redirected after the port-backlog delivery: "phân tích/so sánh cách viết
code/tính năng của cả 2 shell để có ý tưởng tối ưu hiệu năng lẫn tính thẩm mỹ" —
compare code-writing/features of BOTH shells for performance AND UI-aesthetics ideas.

## What was done
- Discovered the missing half of the evidence: iNiR's real UI lives in **inir-hub**
  (families ii/iris/waffle, themes, widgets) — the base repo carries services only.
  Cloned hub @ 299578d locally; agent-1 clones it machine-side in T04.
- 3 more Explore subagents: E7 design system (tokens, MaterialShape/morph.js, Lume
  consumers, settings preview scenes, notification anatomy), E8 perf-pattern census
  (WidgetPowerManager, CavaService refcounting, IrisImage decode policy, OrganicIdleClock,
  timer/process/animation counts base vs hub), E9 LME perf posture (FrameLogger,
  render-lifetime 406→787 MB plateau, GlassMaterial 48-ancestor nesting walk, 80-Timer
  census, theme token inventory).
- Wrote `07-performance-patterns.md` (18-pattern comparison, new PB-31..PB-40,
  "what LME does better" keep-list) and `08-aesthetic-ideas.md` (token comparison,
  palette-neutral ideas PB-41..PB-50, do-not-copy list) into the owner's
  `~/agent-collab/reports/inir-vs-lme/`; 00-summary addendum + README updated; T04
  verification dispatched.

## Highest-value findings (durable)
- iNiR's core perf trick is NOT batching alone — it's **animation-activity gating**:
  any started animation wakes EVERY shell window (QSGThreadedRenderLoop::
  animationStarted, cited in AbstractBackgroundWidget.qml:243-253); their power
  predicate chain powerActive→motionActive→animationsActive is the pattern LME lacks
  for its ambient layer.
- **IrisImage decode policy** (hub families/iris/components/IrisImage.qml:9-29):
  DPR-aware decode rounded UP to 32px steps + 2px mipmap twin padding — prevents
  re-decode-per-morph-frame and texture-cache poisoning. Directly relevant to LME's
  morphing island.
- iNiR's polish is palette-neutral: concentric radius helper, tnum numerals,
  notification interaction physics (stack fan/drag-dismiss/hover-cancel/resize grace),
  settings preview scenes ("each option drawn as what it changes"), OSD icon that
  scales with value. All adoptable into LME's fixed Dracula + glass language.
- LME keeps real advantages: blur-region unions vs iNiR's full-surface blur (its own
  docs warn weaker GPUs), telemetry culture, retained popups, clipboard engine,
  size-cap discipline. Do not "fix" these toward iNiR.

## Tooling notes
- Same oc2.py bridge worked across the turn; sandbox /home/z/my-project persisted
  (clones + report drafts + oc_env.sh), /tmp did not matter this time.
- Reminder enforced: files written in a PREVIOUS turn must be Read again before
  Edit/Write in a new turn — plan Read+Edit pairs when updating logs/READMEs.
