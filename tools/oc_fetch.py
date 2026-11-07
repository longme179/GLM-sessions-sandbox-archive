#!/usr/bin/env python3
"""Fetch a file from the remote OpenCode machine via chunked base64 shell.

Usage: oc_fetch.py <session_id> <remote_path> <local_path>
Env: OC_URL, OC_AUTH (user:pass)
"""
import base64
import json
import os
import re
import sys
import time
import urllib.request

SID = sys.argv[1]
REMOTE = sys.argv[2]
LOCAL = sys.argv[3]
CHUNK = 38000


def call(path, method="GET", body=None, timeout=120):
    req = urllib.request.Request(os.environ["OC_URL"] + path, method=method)
    req.add_header("Authorization",
                   "Basic " + base64.b64encode(os.environ["OC_AUTH"].encode()).decode())
    if body is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(body).encode()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def shell(cmd):
    call(f"/api/session/{SID}/shell", method="POST", body={"command": cmd})
    marker = 'command="' + cmd + '"'
    # wait for result in inbox (newest-first, exact full-command match)
    for _ in range(25):
        time.sleep(1.5)
        try:
            inbox = call(f"/api/session/{SID}/inbox", timeout=60)
        except Exception:
            continue
        for m in reversed(inbox.get("data", [])):
            t = m.get("payload", {}).get("text", "")
            if marker in t:
                return t
    return None


def extract(payload, tag):
    # output lies between the shell-tag close and </shell>; use unique markers
    m = re.search(rf"^{tag}BEG\n(.*?)\n{tag}END\s*$", payload, re.S | re.M)
    return m.group(1) if m else None


total_b64 = None
p = shell(f"base64 -w0 {REMOTE} > /tmp/fetch.b64; wc -c < /tmp/fetch.b64")
if p:
    m = re.search(r'">\s*(\d+)\s*</shell>', p)
    if m:
        total_b64 = int(m.group(1))
if not total_b64:
    print("FAIL: could not determine size; last payload:", (p or "")[:300])
    sys.exit(1)
print(f"remote b64 size: {total_b64}")

parts = []
pos = 1
idx = 0
run_stamp = f"{int(time.time() * 100) % 100000:05d}"
while pos <= total_b64:
    end = min(pos + CHUNK - 1, total_b64)
    tag = f"K{run_stamp}x{idx:02d}X"
    cmd = f"echo {tag}BEG; cut -c{pos}-{end} /tmp/fetch.b64; echo {tag}END"
    p = shell(cmd)
    if not p:
        print(f"FAIL: no payload for chunk {idx}")
        sys.exit(1)
    data = extract(p, tag)
    if data is None:
        print(f"FAIL: markers not found in chunk {idx}; payload head:", p[:200])
        sys.exit(1)
    parts.append(data.strip())
    print(f"chunk {idx}: {len(data.strip())} chars (want <= {end-pos+1})")
    pos = end + 1
    idx += 1

b64 = "".join(parts)
print(f"total fetched: {len(b64)}")
raw = base64.b64decode(b64)
with open(LOCAL, "wb") as f:
    f.write(raw)
print(f"saved {LOCAL}: {len(raw)} bytes")
