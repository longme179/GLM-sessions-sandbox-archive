#!/usr/bin/env python3
"""Find the collaborator session: probe session message tails for verify/#151 keywords."""
import base64, json, os, sys, urllib.request

url = os.environ["OC_URL"]
auth = "Basic " + base64.b64encode(os.environ["OC_AUTH"].encode()).decode()

def get(path, timeout=20):
    r = urllib.request.Request(url + path)
    r.add_header("Authorization", auth)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.load(resp)

sids = sys.argv[1:]
for sid in sids:
    try:
        msgs = get(f"/api/session/{sid}/message").get("data", [])
    except Exception as e:
        print(f"{sid}: ERR {e}")
        continue
    tail = msgs[-12:] if len(msgs) >= 12 else msgs
    hit = ""
    last_user = ""
    for m in reversed(tail):
        txt = json.dumps(m)[:300]
        low = txt.lower()
        if not last_user and m.get("role") == "user":
            last_user = (m.get("parts") and json.dumps(m["parts"])[:200]) or ""
        if any(k in low for k in ("#151", "verify-lock", "agent-collab", "journal", "phase 3", "locksettings")):
            hit = txt[:200]
            break
    print(f"{sid} | msgs={len(msgs)} | hit={hit!r}")
