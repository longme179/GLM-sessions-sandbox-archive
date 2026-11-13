#!/usr/bin/env bash
# oc-shell.sh — remote real-machine executor via the OpenCode GLOBAL /api/shell
# endpoint (no agent session, no model tokens). Hardened variant of rsh.sh:
# curl -K config files break on some hosts (curl 8.14.1) — auth goes through
# a chmod-600 header file passed as `curl --header @file`.
#
# Usage:   oc-shell.sh <timeout_ms> <command...>   (command passed as single string)
# Env:     OC_URL   gateway base URL               (e.g. https://host.example)
#          OC_HDR   path to the auth header file   (default ~/.oc-auth-header)
#                   containing one line: Authorization: Basic <base64(user:pass)>
#          OC_CWD   remote cwd for the command     (default $HOME)
# Setup:   printf 'Authorization: Basic %s\n' "$(printf 'user:pass' | base64 -w0)" > ~/.oc-auth-header
#          chmod 600 ~/.oc-auth-header
set -u
BASE=${OC_URL:?set OC_URL}
HDR=${OC_HDR:-$HOME/.oc-auth-header}
CWD=${OC_CWD:-$HOME}
TIMEOUT_MS=${1:?timeout_ms}
CMD=${2:?command}
[ -f "$HDR" ] || { echo "missing $HDR (see header comment for setup)" >&2; exit 1; }

resp=$(curl -s --header @"$HDR" -X POST "$BASE/api/shell" -H "Content-Type: application/json" \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"command": sys.argv[2], "cwd": sys.argv[3], "timeout": int(sys.argv[1])}))' "$TIMEOUT_MS" "$CMD" "$CWD")")
id=$(printf '%s' "$resp" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["id"])' 2>/dev/null) || { echo "SHELL_SPAWN_FAILED: $resp"; exit 1; }

# Poll until exited or overall wall limit (timeout + 20s grace).
wall=$(( TIMEOUT_MS / 1000 + 20 ))
for _ in $(seq 1 $(( wall * 2 ))); do
  sleep 0.5
  status=$(curl -s --header @"$HDR" "$BASE/api/shell/$id" | python3 -c 'import json,sys; d=json.load(sys.stdin)["data"]; print(d["status"], d.get("exit", ""))')
  case "$status" in exited*) break ;; esac
done

curl -s --header @"$HDR" "$BASE/api/shell/$id/output" | python3 -c '
import json,sys
d = json.load(sys.stdin)["data"]
sys.stdout.write(d["output"])
if d.get("truncated"): sys.stdout.write("\n[TRUNCATED]\n")'
st=${status%% *}; ex=${status#* }
[ "$st" = "exited" ] || { echo; echo "[oc-shell.sh] status=$st (wall limit)"; exit 124; }
exit "$ex"
