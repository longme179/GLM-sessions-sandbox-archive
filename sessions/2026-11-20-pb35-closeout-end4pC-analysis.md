# Session 2026-11-20 (Agent-2) — PB-35 closeout: push+PR#176, model switch chain, worktree cleanup; end4-pC comparative analysis

Continuation of the Agent-1/Agent-2 collaboration. Context files:
`knowledge/a4-active-state.md` (prior era), `journal/` (evidence backbone),
`knowledge/lme-shell-state.md` (updated this session — read its
"Session 2026-11-20" section for the current tree state).

## 1. PB-35 closeout (screenshot pipeline -> flameshot)

- Pushed branch `fix/screenshot-flameshot` (7 commits, `769b6aa..0871cef`) to
  `origin` and opened **PR #176** ("feat(capture): flameshot replaces the
  shell screenshot pipeline (PB-35)") — gh CLI as `longme179` via the raw
  shell channel; body file `/tmp/pb35-pr-body.md` (Summary / Validation /
  Breaking notes).
- Owner merged it at **2026-11-20T08:28:02Z**; desktop main = `1f0880c`,
  in sync with origin. The deployed live tree IS this main (deployed in the
  PB-35 session, live-verified then).
- Worktree cleanup (owner-authorized): `git worktree remove ~/lme-pb35`
  (clean) + `git branch -d fix/screenshot-flameshot` (was 0871cef).
  NOTE: ~30 older worktrees remain under `~/glm-work/` and
  `~/lme-worktrees/` (a4b/a4c/q5 verify trees, mostly detached HEAD).
  Not touched — owner never asked; candidates for a later owner-approved
  cleanup pass.

## 2. Model switch chain for the OpenCode gateway (free tier)

- Session-old model `openrouter/baidu/ernie-5.5-flash-preview:free` hit
  **"Free usage limit reached"** at 05:36Z (OpenCode-account free tier, NOT a
  missing OpenRouter key — there is no provider API key anywhere; free models
  route through OpenCode's own gateway). Fresh sessions then fell to the paid
  default `opencode/gemini-4-neon` with zero credits -> 402.
- Restored the free model via per-session Model.Ref (see
  lessons-learned.md #11), then set the default in
  `~/.config/opencode/opencode.json` + `systemctl --user restart
  opencode-server.service`. **Port 49374 survives restarts**; the Tailscale
  funnel mapping stays valid (probe both URLs after any restart anyway).
- New handoff (owner, 2026-11-20) priority list: `opencode/deepseek-v4.1-flash-free`
  first, then `openrouter/particle-ai/particle-1:free`,
  `openrouter/inclusionai/ling-3.2-flash:free`, ernie, nemotron.
  Default switched to deepseek-v4.1-flash-free; end-to-end verified with a
  plain (no-model) session + prompt -> `DEFAULT-OK` served by deepseek.
- `oc2.py newsess` now always attaches the model ref (env `OC_MODEL_ID` /
  `OC_PROVIDER`, defaults deepseek) — updated in this repo's `tools/oc2.py`.

## 3. Roadmap review (owner request: "where are we in completing the shell")

- `docs/ROADMAP.md` closed **100% on 2026-11-01** (owner accepted 10/10
  checkpoints incl. aggregate RAM <=400 MB). Post-closure rule: one named
  boundary per authorization, never reopen the whole project.
- Post-roadmap hardening series, all merged: a4c fixes (#169-171), PB-31
  ambient power gating (#172), PB-32 timer gating (#173), PB-33 SmartImage
  DPR decode (#174), PB-34 lock-reload-recovery (#175), PB-35 flameshot (#176).
- Remaining deferrals are owner decisions, not debt: 6/16 Settings pages
  legacy, 68/147 pref keys legacy, 14/89 backend IDs, Q6 backend-retirement
  proposal parked. Review record: sandbox
  `download/roadmap-review-2026-11-20.md` (Vietnamese, owner-facing).

## 4. New task: comparative analysis vs end4-pC (owner request)

Cloned both repos depth-1 into the Agent-2 sandbox (`refs/`), 20-11-2026:

- **end4-pC** = pctrade's heavily extended fork of end-4's illogical-impulse
  (Material-You Hyprland Quickshell). Real GitHub stats via gh: **3,860
  stars / 255 forks**, created 2026-04-07, last push 2026-11-16 (PR #263).
  NOT standalone (requires ii installed). Arch-centric.
- Measured LOC: end4-pC QML 105,312 / py 6,816 / bash 4,198 / js 4,833;
  lme QML 19,708 / py 11,266 / js 3,984 / sh 948. lme's JS is mostly its own
  shape library (`qml/components/shapes/`, ~2.6k lines) — lme already HAS a
  shape library; the gap is application breadth, not tooling.

Key verdicts (full report: sandbox
`download/bao-cao-so-sanh-lme-shell-va-end4pC.docx` + .pdf, 15 pages,
Vietnamese; charts + 11 tables; postcheck 0 errors):

- end4-pC wins: feature breadth (AI assistant w/ 3 providers + screen
  translation, 13 GPU wallpaper transitions, live wallpapers, online
  wallpaper sources, 15+ desktop widgets w/ image-analysis placement, OSK,
  football/booru toys), design-system completeness (matugen dynamic colors
  from wallpaper propagated to GTK/Qt/kitty/icons, M3-Expressive motion
  tokens + animation factory, 185 shared widgets), i18n (14 languages),
  community preset gallery w/ secret-scrubbing.
- lme wins: engineering discipline (1,454-test battery, arch ratchet, G0
  gates), deploy tooling (plan/install/rollback + doctor + COPR), resource
  budgeting (<=400 MB measured), docs (68 files), safe-by-design (command
  allowlist, strict preset schema), and deeper *practical* system
  integration (VPN/WireGuard/hotspot/IP-DNS editor, per-app audio routing,
  reversible battery saver, device batteries, Lenovo charging modes).
- end4-pC red flags worth remembering: 891 LOC of tests total (one bash
  script), no CI/packaging, 101 singletons + 1,057-line Config.qml god-file,
  157 inline `bash -c`, hardcoded uguu.se upload, keyring password via env
  var, DotsUpdater self-update runs git clone + exec.
- Improvement recommendation (owner question "backend or UI?"): **UI/design
  system**, boundary-by-boundary. P1 = wallpaper->theme dynamic colors (all
  pieces exist in Gowall utilities!), README sync after PB-35 (stale
  Satty/Swappy rows), Motion factory upgrade. P2 = selective wallpaper
  transitions, richer desktop widgets, bidirectional config hot-reload (the
  one worthwhile BACKEND job — copy end4-pC's schema-as-defaults JsonAdapter
  pattern), i18n skeleton + Vietnamese. P3 = AI panel, community preset
  gallery, Q6 backend retirement.

## 5. Archive updates made this session

- `tools/oc2.py`: replaced with Agent-2 sandbox version (adds `newsess` with
  Model.Ref + model env vars, `sessions` list command).
- `knowledge/lessons-learned.md`: appended #11-#14 (Model.Ref shape, restart
  semantics, free-tier routing, PR-body-via-file pattern).
- `knowledge/lme-shell-state.md`: new "Session 2026-11-20" section (current
  tree/PR/model state).
- `knowledge/a4-active-state.md`: supersession banner at top.
- This session record.

## 6. Open items for the next session

- Owner decides the next boundary; my recommendation stands: P1 dynamic
  colors from wallpaper first (all pieces already exist in Gowall).
- README Features table still mentions Satty/Swappy + in-shell image
  annotation (stale after PB-35) — small docs sync PR pending.
- ~30 stale worktrees on the desktop (owner call).
- Rotate the OpenCode gateway password when the collaboration closes.
