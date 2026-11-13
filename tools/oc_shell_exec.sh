#!/usr/bin/env bash
# Direct /api/shell executor for the OpenCode gateway (agent-free remote commands).
# Auth: curl header config at /tmp/oc_auth (restore from the private .oc-auth copy).
# Usage: oc_shell_exec.sh <timeout_ms> "<command>"
set -u
BASE="https://eceb57eda0919593.x3v7ggvsseh7.opentunnel.xyz"
TIMEOUT_MS=${1:?timeout_ms}
CMD=${2:?command}
[ -f /tmp/oc_auth ] || { echo "missing /tmp/oc_auth"; exit 1; }

resp=$(curl -s --header @/tmp/oc_auth -X POST "$BASE/api/shell" -H "Content-Type: application/json" \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"command": sys.argv[2], "cwd": "/home/kimhoanglong", "timeout": int(sys.argv[1])}))' "$TIMEOUT_MS" "$CMD")")
id=$(printf '%s' "$resp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["id"])' 2>/dev/null) || { echo "SHELL_SPAWN_FAILED: $resp"; exit 1; }

# Poll until exited or overall wall limit (timeout + 20s grace).
wall=$(( TIMEOUT_MS / 1000 + 20 ))
for _ in $(seq 1 $(( wall * 2 ))); do
  sleep 0.5
  status=$(curl -s --header @/tmp/oc_auth "$BASE/api/shell/$id" | python3 -c 'import json,sys; d=json.load(sys.stdin)["data"]; print(d["status"], d.get("exit", ""))')
  case "$status" in exited*) break ;; esac
done

curl -s --header @/tmp/oc_auth "$BASE/api/shell/$id/output" | python3 -c '
import json,sys
d = json.load(sys.stdin)["data"]
sys.stdout.write(d["output"])
if d.get("truncated"): sys.stdout.write("\n[TRUNCATED]\n")'
st=${status%% *}; ex=${status#* }
[ "$st" = "exited" ] || { echo; echo "[oc.sh] status=$st (wall limit)"; exit 124; }
exit "$ex"
