#!/usr/bin/env python3
"""Fetch full text of specific message id(s) from an opencode session."""
import json, os, sys, urllib.request

url = os.environ["OC_URL"]
auth = open("/tmp/oc_auth").read().strip()
sid = sys.argv[1]
mids = set(sys.argv[2:])
r = urllib.request.Request(url + f"/api/session/{sid}/message")
r.add_header("Authorization", auth.split(": ", 1)[1])
with urllib.request.urlopen(r, timeout=30) as resp:
    msgs = json.load(resp)["data"]
msgs.sort(key=lambda m: m["time"]["created"])
for m in msgs:
    if m.get("id") in mids:
        full = "".join(c.get("text", "") for c in m.get("content", []))
        print(f"===== role={m.get('role') or m.get('type')} id={m.get('id')} =====")
        print(full)
