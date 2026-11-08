---
name: codebase-annotate-map
description: Annotate an entire codebase with comments and build a WORKSPACE_MAP.md relationship map through a remote OpenCode agent, with machine proof of zero behavior change. Use when the user asks for a documentation pass, code annotation, or a workspace/module map of lme-fedora-niri-qs (or any repo reachable via the OpenCode gateway).
---

# Codebase annotation + workspace mapping (comments-only, evidence-first)

Owner-authorized documentation pass. Produces: comment/docstring headers on
every original source file, greppable coupling tags, and
`docs/WORKSPACE_MAP.md`. Hard rule: ZERO behavior change, proven by machine.

## Process (drive the remote agent phase by phase, one prompt per phase)

0. **Survey + baseline.** Clean git status required; branch
   `docs/annotate-and-map` from main. Record HEAD SHA, run the existing
   battery (check.sh / architecture check / full unittest / G0) verbatim to
   files in `/tmp/<notes-dir>/`. Compute a HEADROOM TABLE first (see trap 1).
1. **Relationship graph before any comment.** Reuse the repo's own scanner
   (`check_architecture.py::graph()`) for static edges (Python AST + QML
   import/qmldir + JSON descriptor entries) — that IS the evidence. Enrich
   with grep for: runtime protocol vocab, config keys, env vars, D-Bus/
   external services, data paths, orchestration scripts, implicit coupling.
2. **Annotate in batches, leaves before core** (components → panels →
   services/settings → scripts domain → scripts core → tests). Per batch:
   headroom check → annotate → log line per file → architecture check →
   commit `docs(comments): <batch>` → never push. Per file: 2-6 line header
   (what/why/who-calls/what-it-calls from graph evidence), why-comments on
   non-trivial logic, tags at coupling points.
3. **The map.** 11 sections: header(SHA+date+tooling) / overview / mermaid
   mindmap / mermaid flowchart LR with edge labels / module index table /
   4-6 main flows with file:line / "change X check Y" table / config+env
   table / glossary / findings(record-only) / open questions. Every row
   labeled `[verified]` or `[inferred]`+reason. No /tmp paths, no session
   refs. Re-verify every file:line against the CURRENT tree (annotation
   shifts lines).
4. **Verification battery (evidence, not claims).**
   - Python: ast.dump comparison vs baseline with docstrings stripped
     (all changed files, must be byte-identical).
   - QML/JS/GLSL/sh: string-aware comment stripper + whitespace
     normalization, before vs baseline, identical.
   - Full test battery re-run must match baseline counts exactly.
   - Flaky test? Reproduce on a BASELINE worktree
     (`git worktree add /tmp/base <SHA>`) — if baseline also fails, it is
     environmental; record as Finding with both verbatim summaries.
   - REL tag sweep: every `REL:` first token must be a real repo path
     (checker script); D-Bus/non-file refs get rewritten as plain comments.
   - `git diff --stat <base>..HEAD`: only source files + the map; forbidden
     zones (config/, docs/, third_party/, .agents/, AGENTS.md) untouched.
5. **Finalize.** AGENTS.md gets a 4-line pointer (read map first, grep REL:,
   update map+tags on change, `git diff <SHA>..HEAD --stat` to refresh).
   Docs commit SEPARATE from comment commits. Never push — owner reviews.

## Tag formats (greppable)

`REL: <repo/path>::<symbol> – why they change together`
`INVARIANT: <what must never break>`
`GOTCHA: <the trap, one line>`

## Traps actually hit (2026-11-09 pass, 445 files)

1. **Size ratchet counts comments.** check_architecture nonblank count
   includes comment lines; many files sit AT their ceiling. Compute
   headroom = ceiling − current per file; headroom-0 files get trailing
   (same-line) comments only — a new line anywhere breaks the gate. Run the
   architecture check after EVERY batch.
2. **Docstring inserted above SPDX/old docstring = stray string expr**
   (AST break, `__doc__` hijack). Always EXTEND the original docstring.
3. **Alphabetical batch splits fail on uniform prefixes** (all test suites
   start `test_`). Enumerate, then split into halves at a recorded boundary.
4. **OpenCode gateway `idle` messages go stale** — after sending a new
   prompt, a naive waiter returns on the PREVIOUS run's idle. Only count
   idles that appear AFTER the last user message (tools/wait2.py).
5. **Agents under-annotate when told "proportionate"** — they skip files
   with existing docstrings. The spec is a short header on EVERY original
   file (what/why/callers/callees); run a coverage audit at the end
   (log-entry per file, "missed 0" or fix).
6. **Agents reference ephemeral note paths** (/tmp/...) in docstrings —
   sweep and rewrite to stable pointers before the docs commit.
7. **Never trust the agent's report** — re-verify every claim yourself via
   the gateway's global /api/shell (rsh.sh): diff stats, AST spot-checks on
   random files, tag counts, forbidden-zone greps.
