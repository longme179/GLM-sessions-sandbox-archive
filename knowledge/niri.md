# niri — capability snapshot

> **Refreshed:** 2026-11-07 · **Verified against:** `niri-wm/niri` main @
> `9955d921` (2026-11-06, shallow clone in `/home/z/my-project/repos/niri`),
> v26.04 release notes, LWN brief, `niri-config` parser source. Latest
> stable: **v26.04, released 2026-04-25** — the exact version running on the
> user's desktop (rpm, installed 2026-10-30). Tag `v26.04` == Cargo version
> `26.4.0` (zero-padding differs; main carries the last released version
> until the next release bump). Refresh this file via
> `skills/SKILL-codebase-docs-updater.md` — never via memory.

## 1. Facts my training data gets WRONG today (read this first)

| Stale belief | Verified reality |
|---|---|
| "niri has no blur / no background effects" | **Blur + background effects are mainline since 26.04** (2026-04-25), for windows AND layer-shell surfaces (§2) |
| "repo is YaLTeR/niri" | Moved to GitHub org **niri-wm/niri** (~20k stars, Feb 2026); wiki published at <https://niri-wm.github.io/niri/>; awesome-niri moved into the org |
| "versioning is 0.1.x" | Calendar `YY.MM` since 25.01: 25.01 → 25.02 → 25.05 (+25.05.1) → 25.08 → 25.11 → 26.04 — roughly quarterly, month = release month; next release not yet out (main = 26.04 + 264 commits) |

Other "since" markers worth remembering: floating windows 25.01;
layer-rules 25.01; layer `shadow` + `geometry-corner-radius` 25.02;
`place-within-backdrop` + `baba-is-float` 25.05; Xwayland via
xwayland-satellite integrated 25.08; background-effects + `popups` blocks +
optional `include` + `layer` matcher 26.04. Community: Matrix
`#niri:matrix.org` + Discord. Upstream recommends shells: DankMaterialShell,
Noctalia (niri alone is not a DE). Min Rust 1.85; `niri.service` no longer
hardcodes `/usr/bin`; dinit files restructured (26.04 packager notes).

## 2. Background effects (since 26.04) — the model that matters for lme-shell

Per-surface `background-effect {}` block inside `window-rule` and
`layer-rule`:

```kdl
background-effect {
    xray true|false   // see semantics below — DEFAULT: auto-ON
    blur true|false   // force-enable / force-disable
    noise 0.05        // pixel noise on the background (fights banding)
    saturation 3      // 0 = desaturated, 1 = normal, 2 = 200%
}
```

Cross-checked against the parser: `niri-config/src/appearance.rs:1059
BackgroundEffectRule { xray, blur, noise, saturation }` — wiki and source
agree exactly.

### The two blur modes (THE critical semantics)

- **xray (DEFAULT — auto-enabled whenever ANY background effect is active):**
  the surface's background becomes a blur of the **wallpaper only, ignoring
  every window below**. It is the cheap path: wallpaper blur is computed once
  and reused (animated wallpaper → recomputed once per frame, still shared
  across all surfaces).
- **`xray false` (non-xray):** the "normal" blur of **everything actually
  below the surface**. Marked **experimental** upstream with known
  limitations: effects **disappear during window open/close animations and
  while dragging a tiled window**; recomputed on every movement or content
  change underneath (expensive).

**This is the X-ray bug's other half.** The glass "background bleeds
through" saga (#77/#94/#95/#96) had two independent wallpaper sources: (1)
the shell's own backdrop sampler — removed architecturally by PR #96; (2)
niri's xray-default blur — `liquid-blur.kdl` sets `xray false` (PR #87
strategy presets). PR #96's architecture — tint + grain painted by the
shell, blur owned by the compositor, ZERO background knowledge in the
shader — is exactly the split niri's docs describe. Bar pills showing
blurred wallpaper sky is CORRECT (bar reserves the exclusive zone; lesson
34).

### How blur gets enabled

1. The client requests it via the **`ext-background-effect` Wayland
   protocol** (blur shape follows the client's requested region exactly,
   including client-side rounded corners). Toolkit support includes
   **Quickshell** and winit; apps/ships: DankMaterialShell, Noctalia,
   Vicinae, foot, kitty, Ghostty. → a Quickshell layer surface can in
   principle request its own blur without any niri config.
2. niri-side via `background-effect { blur true }` rule — then blur follows
   `geometry-corner-radius`.
Global kill-switch: top-level `blur { off }` disables ALL blur including
protocol requests.

### `popups` block (since 26.04)

`window-rule`/`layer-rule` can carry `popups { opacity …;
geometry-corner-radius …; background-effect { … } }` for the surface's
xdg-popups (opacity applies ON TOP of the parent rule's). Popup effects
default **non-xray**. Covers only real xdg-popups — NOT input-method
popups (Fcitx), and NOT shells that draw "popups" as ordinary layer
surfaces. lme-shell draws its popups as layer surfaces, so they need their
own layer-rules — which `config/niri/popup-blur.kdl` already provides.

### Global `blur {}` (top-level; defaults shown)

```kdl
blur {
    // off        — disable ALL blur (protocol requests included)
    passes 3     // dual-kawase down/up-sample passes; more = smoother + GPU
    offset 3     // pixel-offset multiplier per pass; smoother at NO GPU cost
    noise 0.02   // anti-banding noise on the blurred background
    saturation 1.5
}
```

Upstream tuning recipe: raise `offset` first (free) until artifacts appear,
THEN add a pass; repeat. User's live values: passes 2, offset 3 — there is
headroom in `offset` before paying GPU for `passes`.

## 3. layer-rule reference card

Source: `docs/wiki/Configuration:-Layer-Rules.md` + `niri-config/src/layer_rule.rs`
(in sync). Matchers: `namespace` (regex, matches anywhere; enumerate live
namespaces with **`niri msg layers`**), `at-startup` (first 60 s), `layer` =
`"background"|"bottom"|"top"|"overlay"` (26.04). Properties:

| Property | Since | Notes |
|---|---|---|
| `opacity` | 25.01 | multiplies the surface's own alpha, per-child (popups show content behind) |
| `block-out-from "screencast"|"screen-capture"` | — | black-out from portals / all capture |
| `shadow { on off softness spread offset x= y= draw-behind-window color inactive-color }` | 25.02 | must be enabled per-rule (layout shadows don't cover layers) |
| `geometry-corner-radius` | 25.02 | rounds the **shadow** corners only |
| `place-within-backdrop` | 25.05 | background-layer wallpaper tools → Overview backdrop |
| `baba-is-float` | 25.05 | joke feature |
| `background-effect` | 26.04 | §2 |
| `popups` | 26.04 | §2 |

`window-rule` has the same `background-effect`/`popups` blocks (26.04) with
window matchers. The user's `lme-shell-deploy.kdl` carries a USER-ADDED
unscoped window-rule (`geometry-corner-radius 28; clip-to-geometry true;
background-effect { blur true }`) applying to ALL windows — not from the
repo, leave it.

## 4. Other capabilities verified this refresh

- Scrollable tiling (per-monitor strips, no cross-monitor overflow), dynamic
  workspaces, Overview (`overview { zoom backdrop-color workspace-shadow }`),
  built-in screenshot UI, floating windows, tabs, live-reloading KDL config
  (`niri msg action load-config-file [--path]`), hotkey-overlay,
  config-notification, clipboard options, gestures (touchpad + mouse; no
  touchscreen gestures yet), Oklab/Oklch gradient borders, custom
  open/close/resize animation **shaders** (`docs/wiki/examples/*.frag`),
  accessibility (AccessKit, screen readers).
- Screencasting via xdg-desktop-portal-gnome: window/monitor casts, dynamic
  cast target, pointer-in-window-cast with metadata (26.04),
  `niri msg casts` monitor + stop-by-IPC (26.04), `block-out-from`.
- Xwayland via xwayland-satellite (25.08); wlr protocols: layer-shell,
  gamma-control, screencopy; mixed DPI; fractional scaling pixel-perfect;
  NVIDIA "seems to work fine".
- 26.04 also brought: optional config `include` (`optional=true`, `~`
  expansion, missing-file warning, still watched), pointer warping while
  view scrolling, IME-in-GTK4-popup fix, Escape cancels drag-and-drop,
  input fixes (high-Hz mouse, trackball scroll in overview, Num Lock
  preserved, libinput plugins), Tracy GPU profiling, push-based rendering
  (2–3× faster on modern, 8× on old laptops), ext-foreign-toplevel-list,
  DMA-BUF in nested niri, VRAM-leak fix, GLES2 blur fix (in main).
- IPC: `niri-ipc` crate + `niri msg` (actions, event stream) — lme-shell
  already consumes events via `scripts/niri_events.py`.

## 5. Unreleased in main (v26.04 + 264 commits @ 2026-11-06 — NOT on the user's rpm)

From the compare page (paged partially — treat as highlights, not
exhaustive): per-output `max-bpc` config + IPC action + 10-bit framebuffer
pixel formats; `map-to-focused-window` tablet option; tablet stylus button
triggers/binds; screenshot-UI selection move (hold Mod); set/unset
fullscreen/maximized-to-edges actions (HEAD commit); recent-window switch
mouse warp; PipeWire 0.10; multigpu color-format copy fix; security-model
wiki page. **Do not design against these until they ship.**

## 6. Sources

- Clone `/home/z/my-project/repos/niri` @ `9955d921` (2026-11-06):
  `README.md`, `docs/wiki/Window-Effects.md`,
  `docs/wiki/Configuration:-Layer-Rules.md`,
  `docs/wiki/Configuration:-Miscellaneous.md` (§blur, lines 332–410),
  `niri-config/src/layer_rule.rs`, `niri-config/src/appearance.rs:1059`,
  `Cargo.toml` (workspace version 26.4.0).
- Release v26.04 (2026-04-25): <https://github.com/niri-wm/niri/releases/tag/v26.04>
- LWN brief: <https://lwn.net/Articles/1069939/>
- Compare v26.04...main (264 commits): <https://github.com/niri-wm/niri/compare/v26.04...main>
