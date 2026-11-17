# Incident 2026-11-16 ~04:35 +07 — sandbox recycle mid-turn (PB-31 start)

## What happened
Right after the owner approved PB-31 and I dispatched T05 (recon), the sandbox was
recycled between two tool calls. Everything untracked under /home/z/my-project was
wiped: work/report (00-08 drafts), work/repos (3 clones), work/prompts+logs,
download/inir-vs-lme backups, archive/ clone, scripts/oc_env.sh (the bridge
credentials). The T05 dispatch died at `source oc_env.sh` — agent-1 never received it.

## What survived
- Tracked files (re-provisioned from the my-project git repo): scripts/oc2.py, .env.
- upload/working-protocol.txt + linux-context-report.md (original session inputs) —
  THE recovery source: it contains the gateway URL (the tunnel provider turned out
  NOT to be trycloudflare — earlier greps had targeted the wrong provider), the
  basic-auth pair, and the GitHub PAT.
- work/prompts/T05-pb31-recon.md (written moments before the reset).
- The owner's machine: all delivered reports/tasks/logs intact (agent-collab/).
- The archive GitHub repo (public): full knowledge base re-clonable.

## Recovery trail (all masked-output, values never printed)
1. zcode rollout/db: only contains the CURRENT session — pre-context data gone.
   Stage 1-3 greps matched only my own turn's text (self-contamination; one regex
   even matched "https://..." as a user:pass pair — lesson below).
2. Archive repo found PUBLIC → re-cloned → recovered knowledge + old tools.
3. upload/working-protocol.txt → extracted OC_AUTH + GH_ARCHIVE_TOKEN (stage 4).
4. OC_URL found via an archive doc mentioning the provider host; extracted from
   the protocol's "Base URL:" line into oc_env.sh (chmod 600).
5. Bridge tested: gateway alive, but session lookup returned null → OC_SID had a
   ONE-CHARACTER TYPO (last char W vs the true S) copied from a context summary.
   GET /api/session list confirmed the real id. Fixed → bridge fully restored.

## Sanitizer lesson (security note)
My stage-4 sanitizer redacted the URL (regex saw https://... as user:pass) but let
the literal "Password: ..." line through into the transcript (Read of the sanitized
copy). The value appeared once in the owner-visible transcript. No external exposure
(transcript is owner-only), but: sanitize by KNOWN KEY NAMES (Password:, Token:,
Authorization:) first, then shape-based regexes. Also: the one-char SID typo proves
session ids must be copied from API output programmatically, never by eye/summary.

## Standing state after recovery
- scripts/oc_env.sh restored (OC_URL/OC_AUTH/OC_SID/GH_ARCHIVE_TOKEN, chmod 600).
- scripts/recover_env{,2,3,4}.py kept as the recovery playbook for future recycles.
- archive/ is a fresh clone of GLM-sessions-sandbox-archive (2caf02d).
- T05 re-put (md5 30ab21dc…) + re-dispatched properly (tool-run background, not `&`).
- Note: shell `&` backgrounding dies with the tool call — always use run_in_background.
