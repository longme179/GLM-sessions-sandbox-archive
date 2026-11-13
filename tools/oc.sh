#!/usr/bin/env bash
# OpenCode remote-agent helper. Credentials come from "${OC_ENV:-$HOME/.oc-env}"
# (600, never printed, deleted when the task ends).
set -euo pipefail
[[ -f "${OC_ENV:-$HOME/.oc-env}" ]] || { echo "missing .oc-env" >&2; exit 2; }
source "${OC_ENV:-$HOME/.oc-env}"
base="$OC_URL"; auth="$OC_AUTH"
sid="${OC_SID:-}"
cmd="${1:-}"; shift || true
j() { python3 -c 'import json,sys; print(json.dumps({"text": sys.stdin.read()}))'; }
case "$cmd" in
  models)   curl -sS --max-time 30 -H "$auth" "$base/api/model" ;;
  agents)   curl -sS --max-time 30 -H "$auth" "$base/api/agent" ;;
  info)     curl -sS --max-time 30 -H "$auth" "$base/api/info" ;;
  new)      sid=$(curl -sS --max-time 30 -X POST -H "$auth" -H 'Content-Type: application/json' \
              -d '{"location":{"directory":"'"$1"'"}}' "$base/api/session" \
              | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["id"])')
            echo "SID=$sid" ;;
  set-model) curl -sS --max-time 30 -X POST -H "$auth" -H 'Content-Type: application/json' \
              -d '{"model":{"id":"'"${1##*/}"'","providerID":"'"${1%%/*}"'"}}' "$base/api/session/$sid/model" ;;
  prompt)   curl -sS --max-time 60 -X POST -H "$auth" -H 'Content-Type: application/json' \
              -d "$(printf '%s' "$1" | j)" "$base/api/session/$sid/prompt" ;;
  wait)     curl -sS --max-time "${1:-300}" -X POST -H "$auth" "$base/api/session/$sid/wait" ;;
  msgs)     curl -sS --max-time 30 -H "$auth" "$base/api/session/$sid/message" ;;
  msg)      curl -sS --max-time 30 -H "$auth" "$base/api/session/$sid/message/$1" ;;
  status)   curl -sS --max-time 30 -H "$auth" "$base/api/session/$sid" ;;
  shell)    curl -sS --max-time "${TMO:-120}" -X POST -H "$auth" -H 'Content-Type: application/json' \
              -d "$(python3 -c 'import json,sys; print(json.dumps({"command": sys.argv[1]}))' "$1")" \
              "$base/api/session/$sid/shell" ;;
  abort)    curl -sS --max-time 30 -X POST -H "$auth" "$base/api/session/$sid/interrupt" ;;
  raw)      shift || true; curl -sS --max-time 60 -H "$auth" "$base/$cmd" "$@" ;;
  *) echo "usage: oc.sh models|agents|info|new DIR|set-model ID|prompt TEXT|wait [SEC]|msgs|msg ID|status|shell CMD|abort" >&2; exit 2 ;;
esac
