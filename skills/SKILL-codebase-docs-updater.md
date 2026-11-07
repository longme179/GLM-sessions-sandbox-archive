# SKILL: refreshing stale knowledge about a codebase (repo → trustworthy docs)

Use this skill whenever: (a) a task designs against an external project whose
capabilities may have moved past GLM's training cutoff (niri, quickshell,
toolchains, fast-moving libs…), (b) the user asks "what can X do now /
lately", (c) a bug smells like the dependency's semantics differ from what
we assumed, or (d) a `knowledge/*.md` snapshot in this archive is stale or
missing. Rule of thumb: **memory about fast-moving projects has an expiry
date; the repo does not.** One clone beats ten theories.

Proof it pays for itself: on 2026-11-07 my confident training belief was
"niri has no blur"; niri 26.04 (Apr 2026) ships a whole background-effect
system whose xray-by-default semantics explained a weeks-long production
bug (the glass X-ray saga) — `knowledge/niri.md` §2.

## Pipeline

1. **Acquire** — the Z.ai sandbox CAN reach GitHub over HTTPS, and PAT
   pushes work too (lesson 30 supersedes lesson 8 for git):
   `git clone --depth 1 https://github.com/<org>/<repo>` into
   `/home/z/my-project/repos/<repo>`. Pin the snapshot:
   `git log -1 --format="%H %cd %s" --date=iso`.
2. **Version floor** — what does the USER actually run? Probe through the
   gateway shell (`<tool> --version`, `rpm -q <pkg>`). Anything only in
   main = "unreleased", record separately, never design against it.
   (niri case: user runs the 26.04 rpm.)
3. **Triage, cheapest truth first**:
   a. `README.md` — the project's own feature claims.
   b. **GitHub Releases** — many repos keep NO CHANGELOG.md in-tree (niri
      doesn't); the releases page IS the changelog. WebFetch the latest tag.
   c. `docs/` + `wiki/` dirs — feature pages; watch their `Since: vX`
      markers against the version floor.
   d. Default/example config (`resources/default-config.kdl` etc.) — ground
      truth for every tunable that exists.
   e. **Parser/CLI source** — `rg "pub struct|struct |enum " <config-crate>/src/`;
      the parser cannot lag the code it parses. Cross-check the wiki against
      it and record the verdict (niri: wiki ↔ `layer_rule.rs` ↔
      `appearance.rs` all agreed).
   f. `<tool> --help` and message subcommands (`niri msg layers`).
4. **Extract with grep-proofs** — `rg -i "<feature>"` across docs AND src
   before believing memory, a blog, OR the wiki. Each claim in the doc
   should be traceable to a file+line or URL.
5. **Cross-verify online** — WebSearch the release (LWN, project blog,
   reddit); cite the URLs in the doc.
6. **Author** `knowledge/<project>.md`, in English (repo language rule):
   - Stamp at top: refreshed date, repo@SHA, latest stable tag + release
     date, what the user's machine actually runs.
   - §1 FIRST: "facts my training data gets WRONG" table — the single most
     valuable section; write it before anything softens the sting.
   - Release timeline, one line per version.
   - Deep-dives only for subsystems this archive's projects actually touch.
   - Config reference cards with copy-pasteable snippets.
   - Gotchas / experimental flags section (e.g. non-xray blur limits).
   - Sources: clone paths + file paths + URLs.
7. **Connect** — every major fact should answer "which decision or bug of
   ours does this explain or change?" (niri xray semantics ↔ PR #96
   architecture validation).
8. **Maintain** (next refresh) — read the existing doc first; WebFetch the
   compare page `vOLD...main`; update deltas only; bump the stamp; don't
   rewrite what didn't change.
9. **Archive** — add the doc to `README.md` Map, append a lesson to
   `knowledge/lessons-learned.md` if something durable was learned, update
   `knowledge/lme-shell-state.md` if runtime facts shifted, commit + push.

## Pitfalls (all seen live)

- Memory is confident AND wrong. The WRONG-beliefs table is the point of
  the whole exercise — never skip it.
- Wiki pages can describe UNRELEASED main features. Reconcile every
  "Since: vX" marker against the user's version floor.
- Shallow clones have no tags and no blame — use the GitHub compare and
  releases pages instead of git internals.
- `api.github.com` rate-limits unauthenticated calls (the compare API
  returned an empty body on 2026-11-07); fall back to the HTML compare
  page via WebFetch.
- Big WebFetches truncate (~30 KB of HTML); page or slice them.
- Distinguish three things: stable tag < main@HEAD < what the user's distro
  actually ships. Design against the floor, note the rest.
- Sandbox filesystem can be slow right after a big clone — small targeted
  commands, not one giant find/rg over the tree.

## Worked example

`knowledge/niri.md` (2026-11-07): a ~1 h refresh that corrected "niri has
no blur", caught the YaLTeR→niri-wm org move and the YY.MM versioning, and
pinned the exact xray-default semantics that retroactively explained the
glass X-ray bug — before that doc, every design conversation about the bug
ran on a pre-blur mental model of niri.
