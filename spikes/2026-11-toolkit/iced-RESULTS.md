=====SPLIT-MARKER=====
# iced 0.13 spike — results

Toolkit spike **C2** for Minewrap: `iced 0.13.1` with **tiny-skia** (CPU) and
`lto=true, codegen-units=1, strip=true`. All code and results live under
`~/dev-memtest/spikes/iced/`; nothing was committed or pushed, and the
Minewrap repo and memtest harness were not modified.

Measured: 2026-11-11, on the workstation described below. Numbers are real
instrument readings, not estimates. Items that could not be verified are
listed explicitly in §8.

---

## 1. Environment (applies to every number in this report)

| Item | Value |
|---|---|
| Display path | **wayland-direct** (Xvfb absent; `sudo dnf install` blocked by password prompt) |
| Compositor | private headless **sway 1.11**, pixman software renderer, `output HEADLESS-1 resolution 1280x800` |
| Wayland socket | `wayland-2` (private instance; user's niri session untouched) |
| Window | 1280×800, mapped and screenshot-verified (`evidence/iced-window.png`, `evidence/initial-top.png`) |
| Kernel | `7.2.15-200.fc44.x86_64` |
| CPU | AMD Ryzen 5 7535HS, 12 threads |
| RAM | 15,520,516 kB total |
| Locale | `en_US.UTF-8` |
| Font | Noto Sans Regular 10 pt (`/usr/share/fonts/google-noto/NotoSans-Regular.ttf`, 621,572 B), embedded via `iced::application::font` and set as default font |
| Renderer | tiny-skia (`default-features = false`, feature `tiny-skia`); antialiasing disabled |
| Sampler | `~/dev-memtest/memsample.py`, 1 Hz, `smaps_rollup` RSS/PSS/USS, process tree = 1 process, no subprocesses |

Because there is no Xvfb, this is a Wayland-direct measurement and must not be
compared across Xvfb↔Wayland without that caveat (per SPEC C4).

**Configurations (default vs tuned):** iced 0.13.1 exposes **no
`accessibility` feature and no accesskit dependency** (verified by inspecting
`iced-0.13.1/Cargo.toml`; only renderer/windowing/runtime features exist).
Therefore the "tuned (accessibility off)" configuration is not available; the
default and tuned builds would be byte-identical. Only one configuration was
measured. This is a deviation from the two-config matrix in the SPEC, recorded
as skipped in §8.

---

## 2. Build, binary and dependency footprint

| Metric | Value |
|---|---|
| Clean build (`cargo clean && time cargo build --release`) | **104.22 s** wall, 12 threads |
| Binary size (release, stripped) | **6,286,144 B** (5.99 MiB) |
| SHA-256 | `872ee1574aa2ef09c405aee8e583c5cedd8078e8288e7ae0148f24e8213e0691` |
| LOC | `src/main.rs` **813** + `src/theme.rs` **185** = **998** Rust LOC |
| System libs (`ldd`, top-level) | `linux-vdso.so.1`, `libgcc_s.so.1`, `libm.so.6`, `libc.so.6`, `ld-linux-x86-64.so.2` — no GTK/Qt/X11/GL stack |

Cargo manifest: iced 0.13.1 with features `tiny-skia`, `advanced`, `smol`
(`smol` is required for `iced::time::every`), plus `chrono` for timestamps.

---

## 3. Memory — idle / burst / stream, 3 runs each

Values are MiB. Cell = **median across the 3 runs [min–max pooled over every
1 Hz sample of all 3 runs]**. `analyze.py` produces this table from the JSON
files in `results/`.

| scenario | metric | median [min–max] | run medians | spread of run medians |
|---|---|---|---|---|
| idle 60 s | RSS | 561.24 [561.14–561.27] | 561.27, 561.14, 561.24 | 0.13 |
| idle 60 s | PSS | 557.52 [557.37–557.56] | 557.52, 557.37, 557.56 | 0.19 |
| idle 60 s | USS | 557.34 [557.19–557.38] | 557.34, 557.19, 557.38 | 0.19 |
| idle 60 s | swap | 0.00 [0.00–0.00] | 0.00, 0.00, 0.00 | 0.00 |
| idle 60 s | threads | 16 [16–16] | 16, 16, 16 | 0 |
| idle 60 s | procs | 1 [1–1] | 1, 1, 1 | 0 |
| burst 2000 | RSS | 578.98 [561.16–579.25] | 578.98, 578.94, 579.25 | 0.31 |
| burst 2000 | PSS | 575.24 [557.41–575.50] | 575.24, 575.20, 575.50 | 0.30 |
| burst 2000 | USS | 575.06 [557.23–575.32] | 575.06, 575.01, 575.32 | 0.30 |
| burst 2000 | swap | 0.00 [0.00–0.00] | 0.00, 0.00, 0.00 | 0.00 |
| burst 2000 | threads | 16 [16–16] | 16, 16, 16 | 0 |
| burst 2000 | procs | 1 [1–1] | 1, 1, 1 | 0 |
| stream 2/s | RSS | 579.09 [578.96–579.22] | 579.09, 578.96, 579.18 | 0.22 |
| stream 2/s | PSS | 575.31 [575.31–575.47] | 575.31, 575.31, 575.42 | 0.11 |
| stream 2/s | USS | 575.13 [575.11–575.29] | 575.12, 575.13, 575.23 | 0.11 |
| stream 2/s | swap | 0.00 [0.00–0.00] | 0.00, 0.00, 0.00 | 0.00 |
| stream 2/s | threads | 16 [16–16] | 16, 16, 16 | 0 |
| stream 2/s | procs | 1 [1–1] | 1, 1, 1 | 0 |

Notes:

- Idle is essentially flat inside every run (RSS constant to the 1 KiB
  resolution of the sampler); the 0.13–0.19 MiB differences are between-run
  baseline shifts.
- The burst `min` column is the **pre-burst** sample (`t=0`); the post-burst
  plateau is ~579 MiB. Ring is capped at 1000 lines, so 2000 inserted lines
  cost only ~17.8 MiB over idle and then stop growing.
- Stream for 60 s ends at the same ~579 MiB plateau as burst; no leak beyond
  the fixed ring.
- **SPEC AC "jitter ≤ 0.15 MiB":** met for RSS idle (0.13) and all inside-run
  samples (≤0.02); PSS/USS idle spread is 0.19 MiB, i.e. **0.04 MiB above the
  AC**, caused by between-run baseline shift rather than sampling noise. Burst
  and stream run-median spreads (0.30/0.22) reflect when the sampler window
  lands relative to the burst, not instability of the plateau. Reported as
  measured, not massaged.

---

## 4. Cold start (exec → first drawn frame)

Instrumentation: stderr `SPIKE start` in `main()` and `SPIKE ready` on the
first `iced::window::frames()` callback after the event loop maps/draws.

| run | cold start |
|---|---|
| 1 | 300 ms |
| 2 | 298 ms |
| 3 | 303 ms |
| **median** | **300 ms** |

One earlier launch inside the user's niri session measured 2377 ms; that is
treated as an environment outlier (compositor/session scheduling) and is
**not** part of the official sway figures. Auto-run launches measured
294–311 ms, consistent with the table.

---

## 5. Console acceptance checklist

| # | Requirement | Verdict | Evidence / note |
|---|---|---|---|
| 1 | Ring exactly 1000 lines, FIFO | **Pass** | `VecDeque`, hard cap 1000; after Burst 2000 header/status show `1000 / 1000` and `SPIKE ... lines=1000`; after 60 s stream still 1000 (`results/stream-r*.app.log`). |
| 2 | Per-level colors (INFO/WARN/ERROR/DEBUG) | **Partial (by design)** | "colored" variant renders one `text` per line with per-level colors (INFO default, WARN amber, ERROR red, DEBUG blue), verified in `evidence/verify-colored.png`; "editor" variant is a single `text_editor` and is monochrome — iced 0.13 `text_editor` cannot color per line. This is the real trade-off the SPEC asked to record. |
| 3 | Native text selection + Ctrl+C copy | **Pass with workaround** | editor variant: native character-level drag selection works (`evidence/editor-selectall2.png`), and Ctrl+C yields the selection into the Wayland clipboard. iced 0.13's widget-level Copy did **not** reach the Wayland clipboard here, so `key_binding` suppresses Copy/Cut and the app writes via `iced::clipboard::write`; verified 209 chars copied. colored variant: custom line-level selection (not native text selection) + Ctrl+C via the same task API, verified 210 bytes (`evidence/colored-selection.png`, `evidence/colored-copy.png`). Q3 HARD REQUIREMENT is only "native" in the editor variant. |
| 4 | Auto-scroll stick + unstick on scroll up; jump-to-latest | **Partial** | Stick-to-bottom verified (burst/stream keep the tail visible, `needs_snap`). Wheel-up sets `stick=false` and reveals the "Jump to latest" button; the code path exists, but wheel injection was unavailable, so unstick and JumpLatest were **not verified empirically**. Dragging the scrollbar does not unstick (known limitation of this spike). |
| 5 | Burst 2000 lines < 1 s without UI freeze | **Pass** | Batched 250 lines/frame over `window::frames()`, ring stays at 1000. Auto runs: 259, 263, 264, 271, 286 ms (`SPIKE burst_complete`); manual button: 5 ms instrumented. All well under 1 s; screenshots show the window responsive (`evidence/iced-auto-burst.png`). |
| 6 | Form two-way binding (Apply renames selected sidebar instance) | **Pass** | 2 `text_input`s + `pick_list` (4 status options) + Apply; name/description/status written back to the selected instance and status bar shows "applied to …" (`evidence/form-filled.png`, `evidence/form-applied.png`). |
| 7 | `--auto`: 10 s → burst 2000 → 60 s stream 2/s → exit | **Pass** | Logs: burst_start at +10.0 s, burst_complete, stream until +70 s, `SPIKE exit elapsed_ms=70008/70092/70094 lines=1000`; process exits. |
| 8 | Noto Sans 10 pt | **Pass** | Custom font loaded from disk, `Font::with_name("Noto Sans")` as default, size 13.0 px = 10 pt @ 96 dpi; `fc-match` confirms NotoSans-Regular. |

Additional verified interactions: colored console Clear empties ring and status;
manual Burst reaches exactly 1000; instance switching drives form contents.

Known visual artifact: after Clear in colored mode, a faint repaint sliver can
remain for one frame until the next scroll/repaint. Cosmetic only, noted rather
than hidden.

---

## 6. Interaction verification method

- Private sway 1.11 on `wayland-2`, `grim` screenshots in `evidence/`.
- Pointer: `/tmp/lme-dev/lme-pointer` (wlr virtual pointer) for clicks/drags.
- Keyboard: `wtype -s 200` (200 ms key hold) — without `-s` the Ctrl modifier
  was intermittently lost; `wtype -s 200 -M ctrl -k c` was used for copy tests.
- Window mapping confirmed via `swaymsg -t get_tree` (1280×800) before every
  screenshot batch.

---

## 7. Ergonomics and porting notes (subjective — not measurements)

What worked well:

- The Elm-style `update`/`view`/`Subscription` model maps cleanly onto
  Minewrap's state-driven UI; form two-way binding and sidebar selection took
  little code.
- `tiny-skia` backend is genuinely dependency-light: 6 system libs, no GL/GTK.
  Release binary is 6.0 MiB and cold start ~300 ms.
- `scrollable::snap_to` + `window::frames()` gives precise control for
  stick-to-bottom and batched burst loading; the 1000-line ring never exceeded
  the memory plateau.

What hurt:

- **Text selection is the weak point.** `text_editor` supports selection but
  is monochrome, read-only-ish styling is awkward, and its built-in Ctrl+C did
  not reach the Wayland clipboard; a custom `key_binding` + `clipboard::write`
  workaround was required. The colored variant needed a hand-written line
  selection model on top of one widget per line.
- No `select` widget in iced 0.13; `pick_list` is the only dropdown.
- No scrollbar-drag detection and no wheel event on the scrollable itself; the
  spike wraps it in `mouse_area` to detect wheel-up. Scrollbar thumb drag will
  not unstick in this implementation.
- Icons, rich text spans, and per-line styling require custom widgets; there is
  no CSS-like styling layer.

Port difficulty for the 12 Minewrap UI components (subjective, 1 = easy):

| Component | Difficulty | Note |
|---|---|---|
| App shell / navigation | Low | `row`/`column` + theme styles |
| Dashboard | Low–medium | cards are containers; charts would need `canvas` |
| Nodes | Medium | table/list + status badges is straightforward |
| Console | **High** | selection + colors + copy + stick + burst are all custom, as above |
| AddInstance | Medium | form widgets exist; validation/flow is manual |
| Properties | Medium | many inputs; two-way binding is verbose but simple |
| Mods | Medium | list + file dialogs would need extra crates/portal |
| JavaPicker | Medium | `pick_list` + detect paths; no native file dialog |
| Select | Low | `pick_list` |
| Settings | Low–medium | form-heavy, no built-in tabs |
| Notifications | Medium | toasts need custom overlay/positioning |
| Wizard | Medium–high | multi-step state machine is fine, modals/overlays are manual |

Overall: viable for Minewrap's console-centric UI, but the console itself is
the riskiest component and needs ~200–300 lines of custom selection/scroll
plumbing (this spike: 813 LOC total including both console variants).

---

## 8. Unverified / skipped / deviations

1. **Tuned (accessibility off) config** — not measurable: iced 0.13.1 has no
   accessibility feature/accesskit. Default and tuned would be identical; only
   one config was built and measured.
2. **Xvfb** — unavailable; `sudo dnf install xorg-x11-server-Xvfb` requires a
   password. Measured wayland-direct instead, as the SPEC fallback allows.
3. **Wheel-up unstick + "Jump to latest" click** — code present, but no wheel
   injection tool was available; not verified end-to-end. Scrollbar drag does
   not unstick (implementation limitation).
4. **Fully native Ctrl+C in the editor** — iced 0.13's built-in binding did not
   reach the Wayland clipboard in this environment; copy works through the
   explicit `clipboard::write` workaround. Marked "pass with workaround", not
   "native pass".
5. **Manual-burst timing (5 ms)** — instrumented queue-drain measurement; it is
   not a human-observed end-to-end latency. The auto-run measurements
   (259–286 ms) are the defensible figures. Both are < 1 s.
6. **Jitter AC** — PSS/USS idle spread is 0.19 MiB vs the 0.15 MiB AC; see §3.
7. **Stream toggle via UI** — `--auto` stream path was measured; the manual
   "Stream 2/s" toggle was exercised visually but its 1 Hz memory trace was not
   separately recorded (same code path as auto stream).
8. **High-DPI / fractional scaling** — only 1.0 scale at 1280×800 was tested.
9. **Long-run leak test beyond 60 s** — not performed; ring-bound behavior
   suggests a plateau, but >60 s was not sampled.
10. **Minewrap repo integration** — intentionally out of scope (Q8); no commit,
    no push, no changes outside `~/dev-memtest/spikes/iced/`.

---

## 9. Reproduction

```bash
cd ~/dev-memtest/spikes/iced
cargo build --release
# private headless sway must already be running on wayland-2 (evidence/sway.conf)
./measure.sh          # cold start ×3, idle/burst/stream ×3
python3 analyze.py    # prints the table in §3
```

Raw evidence: `results/*.json`, `results/csv_*.csv`, `results/*.app.log`,
screenshots in `evidence/`, sway config/log in `evidence/sway.conf` and
`evidence/sway.log`.
