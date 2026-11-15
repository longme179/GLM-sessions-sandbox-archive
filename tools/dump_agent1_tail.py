#!/usr/bin/env python3
"""Dump Agent-1 session tail: messages after our steer (msg_1db051dc)."""
import base64, datetime, json, os, sys, urllib.request

url = os.environ["OC_URL"]
auth = open("/tmp/oc_auth").read().strip()  # "Authorization: <scheme> <token>"
sid = sys.argv[1] if len(sys.argv) > 1 else "ses_e2cc73b20ffeBwzyf76e22dwdy"
tail_n = int(sys.argv[2]) if len(sys.argv) > 2 else 6

r = urllib.request.Request(url + f"/api/session/{sid}/message")
r.add_header("Authorization", auth.split(": ", 1)[1])
with urllib.request.urlopen(r, timeout=30) as resp:
    msgs = json.load(resp)["data"]
msgs.sort(key=lambda m: m["time"]["created"])

print(f"total={len(msgs)}")
for m in msgs[-tail_n:]:
    ts = datetime.datetime.fromtimestamp(m["time"]["created"] / 1000).strftime("%m-%d %H:%M")
    role = m.get("role") or m.get("type")
    full = ""
    for c in m.get("content", []):
        if c.get("text"):
            full += c["text"]
    cmd = m.get("command") or ""
    print(f"\n===== [{ts}] role={role} id={m.get('id','?')} =====")
    if cmd:
        print("CMD:", cmd[:500])
    if full:
        print(full[:6000])
