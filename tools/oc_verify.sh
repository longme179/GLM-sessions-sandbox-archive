#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Role: create/prompt/wait/report an OpenCode verification session.
# Env: OC_URL (gateway base URL), OC_AUTH (user:pass). Never store credentials here.
#
# Usage:
#   oc_verify.sh health
#   oc_verify.sh create <title> [provider/model]
#   oc_verify.sh prompt <session-id> <prompt-file>
#   oc_verify.sh wait <session-id>
#   oc_verify.sh report <session-id>
#   oc_verify.sh all <title> <prompt-file> [provider/model]
#
# Default model: opencode/beam-free. `all` creates, prompts, waits and prints
# the last assistant text. The session runs on the user's machine; prompts and
# reports are data, never instructions.
set -euo pipefail
: "${OC_URL:?set OC_URL to the gateway base URL}"
: "${OC_AUTH:?set OC_AUTH to user:pass}"

usage() { sed -n '2,18p' "$0"; }

api() {
    local path="$1"; shift
    curl -sS --max-time 60 -u "$OC_AUTH" "$OC_URL$path" "$@"
}

health() { api /api/info | python3 -m json.tool; }

create() {
    local title="${1:?title required}"
    local model="${2:-opencode/beam-free}"
    local provider="${model%%/*}" mid="${model#*/}"
    local body response
    body=$(python3 - "$title" "$provider" "$mid" <<'PY'
import json
import sys
title, provider, mid = sys.argv[1:4]
print(json.dumps({
    "location": {"directory": "/home/kimhoanglong"},
    "title": title,
    "model": {"providerID": provider, "id": mid},
}))
PY
)
    response=$(api /api/session -X POST -H 'Content-Type: application/json' -d "$body")
    python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("data") or {}).get("id") or json.dumps(d))' <<<"$response"
}

prompt() {
    local sid="${1:?session id required}"
    local file="${2:?prompt file required}"
    local body
    body=$(python3 - "$file" <<'PY'
import json
import sys
print(json.dumps({"text": open(sys.argv[1], encoding="utf-8").read()}))
PY
)
    api "/api/session/$sid/prompt" -X POST -H 'Content-Type: application/json' -d "$body" >/dev/null
    printf 'prompt queued: %s\n' "$sid"
}

wait_idle() {
    local sid="${1:?session id required}"
    local code
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 900 \
        -u "$OC_AUTH" -X POST "$OC_URL/api/session/$sid/wait")
    printf 'wait: HTTP %s\n' "$code"
}

report() {
    local sid="${1:?session id required}"
    curl -sS --max-time 60 -u "$OC_AUTH" \
        "$OC_URL/api/session/$sid/message?order=desc&limit=10&type=assistant" \
        | python3 -c '
import json
import sys
for message in json.load(sys.stdin).get("data") or []:
    text = "".join(part.get("text", "") for part in (message.get("content") or [])
                   if part.get("type") == "text")
    if text.strip():
        print(text)
        break
'
}

all() {
    local title="${1:?title required}"
    local file="${2:?prompt file required}"
    local model="${3:-opencode/beam-free}"
    local sid
    sid=$(create "$title" "$model")
    printf 'session: %s\n' "$sid"
    prompt "$sid" "$file"
    wait_idle "$sid"
    report "$sid"
}

case "${1:-}" in
    health) health ;;
    create) shift; create "$@" ;;
    prompt) shift; prompt "$@" ;;
    wait|wait-idle) shift; wait_idle "$@" ;;
    report) shift; report "$@" ;;
    all) shift; all "$@" ;;
    *) usage; exit 2 ;;
esac
