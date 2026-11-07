#!/usr/bin/env bash
# rsh.sh — run ONE raw shell command on the user's desktop via the OpenCode
# gateway's global /api/shell (no agent session involved).
#
# Usage:  rsh.sh "command" [timeout_ms]
# Env:    OC_URL (https://host), OC_AUTH (user:pass)
set -u
[ -z "${OC_URL:-}" ] || [ -z "${OC_AUTH:-}" ] && { echo "ERROR: set OC_URL and OC_AUTH" >&2; exit 1; }
GW="$OC_URL"; AUTH="$OC_AUTH"
TIMEOUT="${2:-60000}"
PAYLOAD=$(python3 -c 'import json,sys; print(json.dumps({"command": sys.argv[1], "timeout": int(sys.argv[2])}))' "$1" "$TIMEOUT")
RESP=$(curl -s -m 90 -u "$AUTH" -X POST "$GW/api/shell" -H 'Content-Type: application/json' -d "$PAYLOAD")
ID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["id"])' <<<"$RESP" 2>/dev/null)
if [ -z "${ID:-}" ]; then echo "ERROR: failed to start shell command" >&2; echo "$RESP" >&2; exit 1; fi
for i in $(seq 1 120); do
  ST=$(curl -s -m 15 -u "$AUTH" "$GW/api/shell/$ID" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["status"])' 2>/dev/null)
  case "$ST" in done|error|exited) break;; esac
  sleep 2
done
CURSOR=0
TOTAL=""
while :; do
  RESP=$(curl -s -m 60 -u "$AUTH" "$GW/api/shell/$ID/output?cursor=$CURSOR&limit=2000000")
  CHUNK=$(python3 -c '
import json,sys
d = json.loads(sys.stdin.read())["data"]
sys.stdout.write(d.get("output") or "")
' <<<"$RESP")
  NEXT=$(python3 -c '
import json,sys
d = json.loads(sys.stdin.read())["data"]
print(d.get("cursor") or 0)
' <<<"$RESP")
  TOTAL="$TOTAL$CHUNK"
  if [ "$NEXT" -le "$CURSOR" ] 2>/dev/null; then break; fi
  CURSOR=$NEXT
  [ -z "$CHUNK" ] && break
done
printf '%s' "$TOTAL"
