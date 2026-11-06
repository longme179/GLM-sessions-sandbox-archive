# SKILL: GitHub workflow (lme repo + this archive)

## Environment constraint (hard fact)

The Z.ai sandbox IP is **blocked by GitHub** (403 even on public repos like
octocat/Hello-World; api.github.com rate-limits to 403). ALL git/gh work must
run on the user's desktop through the OpenCode gateway — either the raw
shell (`tools/rsh.sh`, `POST /api/shell`) or the agent
(`gh auth login --with-token` inside a prompt). Verify PRs from the sandbox
by asking the agent for `gh pr view N --json ...` output, not by curling
api.github.com.

## lme-fedora-niri-qs flow (per issue/PR)

1. Branch from `main`: `feat/<topic>` or `fix/<topic>`, conventional commits
   (`feat(glass): ...`, `fix(equalizer): ...`).
2. Validation battery green (see the Quickshell skill) + grim visual proof.
3. PR body: describe the user-visible bug/feature first, then the mechanism.
   Reference issues precisely:
   - `Closes #NN` — autocloses the issue on merge (only when the issue is
     fully done)
   - `Refs #NN` — related, stays open
   - `Follow-up to #NN` — regression fix of a merged PR
4. Merge immediately after review approval (merge commit, `Merge pull
   request #N from ...`), delete the branch, checkout `main`, confirm
   `git log --oneline`.
5. Add the CHANGELOG entry in the SAME PR (## Unreleased section, one entry
   per user-visible change; never rewrite released entries).
6. Verification: `gh pr view N --json number,state,mergedAt,mergeCommit,title`.

PRs also include an honest Verification section: machine-verified items vs
"user-side checks remaining" (things needing the human's live screen — lens
motion feel, preset cycling, battery saver). Never claim the latter as done.

## This archive repo (GLM-sessions-sandbox-archive)

- Push from the desktop too (same constraint). Transfer files byte-exactly
  (base64 through the raw shell), never retyped by the agent.
- Direct commits to `main` are fine here (no PR ceremony — it is GLM's own
  playground). Keep the token in the push URL only for the duration of the
  command; the desktop clone's origin must stay a clean URL.
- End of session: refresh `knowledge/`, commit, push.

## Token discipline (unchanged across all repos)

- GitHub PATs: `printf %s\\n "<token>" | gh auth login --with-token` via
  prompt, or write to `/tmp/.ghtoken` (runtime-only) for API scripts.
- Never in files, commits, PR text, issue text, or archived output.
- 401 → stop and report; never guess or retry with variations.
