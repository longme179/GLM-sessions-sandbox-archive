# iNiR ↔ LME port map (2026-11-16, pins: iNiR@2836543 / LME@7bc362d)

Durable area map for future sessions. Full report on the owner's machine:
`~/agent-collab/reports/inir-vs-lme/` (00-06 + machine-facts + meta.json).

## Already ported into LME (do not re-recommend)
- Settings window + registry + bar groups + Material appearance + capsule/islands
  (original port @48cdcec, `lme:docs/INIR_PORT.md`), clipboard + Activity island,
  wallpaper browser/matugen palette, desktop upgrades (`lme:docs/DESKTOP_UPGRADES.md`).
- Lock screen phases 1-3 (PRs #146-#151): LockState/LockContext/LockSurface/
  LockWallpaper/LockLoginView + idle native handshake + lock settings
  (`lme:docs/STATE.md` "In progress" section).
- A1 undo-first (PR #152), A2 DankSocket vendored (#153), A7 notification ingress
  policies (#154), A12 clipboard ingest policies (#155), A4 motion tokens + island
  morph + radius (PRs #165-#167), capture overlay gate fix (#156), media card (#160-#164).

## Ranked port backlog (report 04; P0/P1)
1. PB-01 frozen-frame region selector — `inir:modules/shared/regionSelector/` (LME's own
   recorded candidate in `lme:docs/FEATURE_PORTS.md:99-120`).
2. PB-02 alt-tab window switcher — `inir:modules/shared/altSwitcher/` (LME has NONE).
3. PB-03 NiriService batching (50ms/200ms) + membership-only reorder + stable workspace
   IDs — `inir:services/NiriService.qml:51-53,830-860,558-596` → into lme NiriState.
4. PB-04 update verify-30s + snapshots + auto-rollback + user-mods —
   `inir:sdata/lib/robust-update.sh:133-172` → extend lme shell_update.py.
5. PB-05 Overview window thumbnails (cached stills via `niri msg action
   screenshot-window` + .part publish + clipboard save/restore) —
   `inir:services/WindowPreviewService.qml` (adapt: no cliphist on the machine).
Then: FadeLoader (A3), StyledTextChange (A6), MemoryPressureService V4 watchdog,
ICS calendar sync (`inir:services/calendar_ics.js` pure JS), MinimizedWindows stash,
GameMode lite (DECISION: no niri-KDL rewrite without owner OK), config journal+rebase
(Q6 legs 2-3 reference; LME chose IpcHandler single-writer D1(a)).

## NOT portable / not worth it
- qs-rs-only: live window pins/streams (ScreencopyView `niriWindowId`/`sourceRect` via
  `SystemInfo.runtimeHas` probes), ambient light sampling.
- Declined by design: plugin host/hub/families, Material You engine + app propagation,
  i18n, Umbriel/Hyprland, AI/YT Music/booru/mascot, WebEngine wallpapers, OSK (no touch).

## LME standing constraints that gate every port
- 250-nonblank file cap + ratchets (`config/architecture.json`); tests local-untracked
  (acceptance = owner-machine G0-G6, `lme:docs/VALIDATION.md` cloud-vs-laptop split);
  AGPL-3.0 with GPLv3 §13 adoption practice (`lme:THIRD_PARTY.md`); never touch user's
  niri config / running session; stdlib-only Python backend; memory ≤400MB steady.
