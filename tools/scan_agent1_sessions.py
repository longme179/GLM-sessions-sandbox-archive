#!/usr/bin/env python3
"""Scan recent remote sessions for the Agent-1 a4b steer / latest activity."""
import datetime, json, os, sys, urllib.request

url = os.environ["OC_URL"]
auth = open("/tmp/oc_auth").read().strip().split(": ", 1)[1]

def get(path, timeout=25):
    r = urllib.request.Request(url + path)
    r.add_header("Authorization", auth)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.load(resp)

def text_of(m):
    out = ""
    for c in m.get("content", []):
        if isinstance(c, dict) and c.get("text"):
            out += c["text"]
    return out

sids = sys.argv[1:]
if not sids:
    all_sessions = get("/api/session")["data"]
    rows = []
    for s in all_sessions:
        ts = (s.get("time") or {}).get("created") or 0
        rows.append((ts, s["id"]))
    rows.sort()
    for ts, sid in rows[-12:]:
        print(datetime.datetime.fromtimestamp(ts / 1000).strftime("%m-%d %H:%M"), sid)
    sids = [sid for _, sid in rows[-12:]]

KEYS = ("A4b", "island-morph", "#166", "A4c", "G4 env", "L2 live")
for sid in sids:
    try:
        msgs = get(f"/api/session/{sid}/message")["data"]
    except Exception as e:
        print(f"{sid}: ERR {e}")
        continue
    msgs.sort(key=lambda m: m["time"]["created"])
    hit = None
    for m in msgs:
        t = text_of(m)
        if any(k in t for k in KEYS):
            hit = t[:120].replace("\n", " ")
    last = msgs[-1] if msgs else None
    last_ts = datetime.datetime.fromtimestamp(last["time"]["created"] / 1000).strftime("%m-%d %H:%M") if last else "?"
    print(f"{sid} | msgs={len(msgs)} | last={last_ts} | hit={hit!r}")
