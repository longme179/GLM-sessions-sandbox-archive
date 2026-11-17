#!/usr/bin/env python3
"""oc_client.py — OpenCode gateway client (v2.3.0+, /api/* routes).

The legacy tools (oc.py, qw.py) target the OLD gateway shape
(POST /api/session with {"location":...}, global /api/shell). The 2026-11-17
gateway runs OpenCode v2.3.0 whose HTTP API is:

  GET  /api/info
  GET  /api/session/active
  POST /api/session                 {"parentID": "...", "title": "..."}
  POST /api/session/{id}/prompt     {"text": "...", "agent": "build"}
  POST /api/experimental/session/{id}/wait   (blocks until idle, 204)
  GET  /api/session/{id}/message    {"limit": N}
  POST /api/session/{id}/interrupt
  GET  /api/session/{id}/permission
  POST /api/session/{id}/permission/{reqID}/reply  {"action": "once"|"always"|"reject"}

Auth (from OpenCode v2.3.0 source, packages/server/src/auth.ts):
  - username is ALWAYS "opencode" (hardcoded in configLayer)
  - accepted as:  Authorization: Basic base64("opencode:"+password)
                  ?auth_token=base64("opencode:"+password)
                  session cookie from a pairing link
  - a pairing session token (expires.<hmac>) also works as the password

Env: OC_URL (https://host), OC_AUTH (opencode:password).
Credentials never hardcoded — hard rule #1 of this archive.

LESSON (2026-11-17): if ALL THREE auth forms return 401 while the middleware
provably receives the request (sec-fetch-mode test), the password is wrong
(rotated). STOP and report — never brute-force (FUTURE-SELF rule).
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def _env():
    url = os.environ.get("OC_URL", "").rstrip("/")
    auth = os.environ.get("OC_AUTH", "")
    if not url or not auth:
        sys.exit("ERROR: export OC_URL and OC_AUTH (opencode:password)")
    return url, auth


def _headers(auth):
    b64 = base64.b64encode(auth.encode()).decode()
    return {
        "Authorization": "Basic " + b64,
        "Content-Type": "application/json",
    }


def call(method, path, body=None, timeout=90):
    url, auth = _env()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url + path, data=data, method=method,
                                 headers=_headers(auth))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def info():
    print(call("GET", "/api/info"))


def active():
    print(call("GET", "/api/session/active"))


def new_session(title=None, parent=None, directory=None):
    body = {}
    if title:
        body["title"] = title
    if parent:
        body["parentID"] = parent
    if directory:  # may be ignored by v2.3.0; kept for forward compat
        body["location"] = {"directory": directory}
    code, data = call("POST", "/api/session", body)
    print(code, json.dumps(data, ensure_ascii=False)[:500] if data else "")


def prompt(sid, text, agent=None):
    body = {"text": text}
    if agent:
        body["agent"] = agent
    print(call("POST", f"/api/session/{sid}/prompt", body, timeout=300))


def wait(sid, timeout=600):
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, _ = call("POST", f"/api/experimental/session/{sid}/wait",
                       None, timeout=60)
        if code == 204:
            print("IDLE")
            return
        time.sleep(5)
    print("TIMEOUT")


def msgs(sid, limit=20):
    code, data = call("GET", f"/api/session/{sid}/message?limit={limit}")
    print(code, json.dumps(data, ensure_ascii=False)[:8000] if data else "")


def message(sid):
    code, data = call("GET", f"/api/session/{sid}/message")
    print(code, json.dumps(data, ensure_ascii=False)[:10000] if data else "")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "info":
        info()
    elif cmd == "active":
        active()
    elif cmd == "new":
        new_session(*sys.argv[2:])
    elif cmd == "prompt":
        prompt(sys.argv[2], open(sys.argv[3]).read() if len(sys.argv) > 3
               else sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == "wait":
        wait(sys.argv[2])
    elif cmd == "msgs":
        msgs(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 20)
    elif cmd == "message":
        message(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)
