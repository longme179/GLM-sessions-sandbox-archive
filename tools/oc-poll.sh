#!/usr/bin/env bash
# Poll the OpenCode session until a new assistant finish=stop message appears
# after a given created-timestamp, or the timeout (seconds) elapses.
set -euo pipefail
TOOLS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

after="${1:?usage: oc-poll.sh AFTER_TIMESTAMP [TIMEOUT_SEC]}"; tmo="${2:-900}"
source "${OC_ENV:-$HOME/.oc-env}"
deadline=$(( $(date +%s) + tmo ))
while (( $(date +%s) < deadline )); do
  out=$(bash "$TOOLS_DIR/oc.sh" msgs | AFTER="$after" python3 -c '
import json,sys,os
d=json.load(sys.stdin)
msgs=d.get("data",d)
if isinstance(msgs,dict): msgs=msgs.get("messages",[])
after=int(os.environ["AFTER"])
done=None; running=False
for m in msgs:
    c=(m.get("time") or {}).get("created") or 0
    if c<=after: continue
    if m.get("type")=="assistant":
        if m.get("finish")=="stop": done=m
        elif m.get("finish")=="error": done=m
        else: running=True
if done:
    print("STATE=DONE")
    for part in (done.get("content") or []):
        if part.get("type")=="text" and part.get("text","").strip():
            print(part["text"])
    if done.get("finish")=="error":
        print("RUN FINISHED WITH ERROR:", json.dumps(done.get("error",{}))[:300])
else:
    print("STATE=RUNNING" if running else "STATE=PENDING")
')
  if grep -q "^STATE=DONE" <<<"$out"; then echo "$out"; exit 0; fi
  sleep 20
done
echo "STATE=TIMEOUT"
