#!/usr/bin/env python3
"""Qwen bridge to the OpenCode gateway. Env: OC_URL, OC_AUTH, [OC_SID].
Commands:
  sh "cmd" [timeout_s]      global agent-free shell (POST /api/shell), prints output
  new [dir]                 create session
  sessions                  list sessions (id, title, updated, outcome)
  prompt <sid> <file>       send prompt from file
  msgs <sid> [n]            last n messages (chronological)
  wait <sid> [secs]         block until idle
  api GET|POST <path> [json]
"""
import base64, json, os, sys, time, urllib.request, urllib.error

URL = os.environ["OC_URL"].rstrip("/")
HDR = {"Authorization": "Basic " + base64.b64encode(os.environ["OC_AUTH"].encode()).decode(),
       "Content-Type": "application/json"}

def api(path, data=None, method=None, timeout=120):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(URL + path, data=body, headers=HDR, method=method or ("POST" if body else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as e:
        return {"__http_error": e.code, "body": e.read().decode()[:2000]}

def sh(cmd, wait=120):
    r = api("/api/shell", {"command": cmd, "timeout": int(wait*1000)})
    if not r or "__http_error" in r: return f"SUBMIT-FAIL {r}"
    sid = r["data"]["id"] if isinstance(r.get("data"), dict) else r.get("id")
    out, cursor, deadline = [], 0, time.time()+wait+30
    while time.time() < deadline:
        o = api(f"/api/shell/{sid}/output?cursor={cursor}&limit=2000000")
        if o:
            d = o.get("data", o)
            chunk = d.get("output") or d.get("text") or ""
            if chunk: out.append(chunk)
            nc = d.get("cursor")
            if isinstance(nc, int): cursor = nc
        st = api(f"/api/shell/{sid}")
        s = (st or {}).get("data", st) or {}
        status = s.get("status")
        if status in ("done", "error", "exited", "completed", "failed"):
            o = api(f"/api/shell/{sid}/output?cursor={cursor}&limit=2000000")
            if o:
                d = o.get("data", o); out.append(d.get("output") or d.get("text") or "")
            return "".join(out) + (f"\n[status={status} exit={s.get('exitCode', s.get('exit'))}]" if status not in ("done","completed") else "")
        time.sleep(1.5)
    return "".join(out) + "\n[TIMEOUT]"

def msgs(sid, n=None):
    r = api(f"/api/session/{sid}/message")
    d = (r or {}).get("data", r)
    if isinstance(d, dict): d = d.get("messages", [])
    d = list(reversed(d))
    return d[-n:] if n else d

def text_of(m):
    parts = m.get("parts") or []
    if parts:
        return "\n".join(p.get("text","") for p in parts if p.get("type")=="text")
    return m.get("text") or ""

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "sh": print(sh(sys.argv[2], int(sys.argv[3]) if len(sys.argv)>3 else 120))
    elif c == "new": print(api("/api/session", {"location":{"directory": sys.argv[2] if len(sys.argv)>2 else "/home/kimhoanglong"}}))
    elif c == "sessions":
        for s in api("/api/session")["data"]:
            t = time.strftime("%m-%d %H:%M", time.localtime(s["time"]["updated"]/1000))
            print(f"{s['id']}  {t}  {s.get('outcome','-'):10s} {s.get('title','')[:70]}")
    elif c == "prompt":
        print(api(f"/api/session/{sys.argv[2]}/prompt", {"text": open(sys.argv[3]).read()}, timeout=180))
    elif c == "msgs":
        for m in msgs(sys.argv[2], int(sys.argv[3]) if len(sys.argv)>3 else 10):
            i = m.get("info", m); role = i.get("role", m.get("type"))
            print(f"--- {role} {i.get('type','')} {i.get('finish','')} ---")
            print(text_of(i)[:6000] or json.dumps(i)[:600])
    elif c == "wait":
        sid = sys.argv[2]; dl = time.time() + (int(sys.argv[3]) if len(sys.argv)>3 else 600)
        while time.time() < dl:
            r = api(f"/api/session/{sid}")
            s = (r or {}).get("data", {})
            tm = s.get("time", {})
            if tm.get("idle") and not tm.get("busy"): print("IDLE", s.get("outcome")); break
            if tm.get("idle") and tm.get("busy") and tm["idle"] > tm["busy"]: print("IDLE", s.get("outcome")); break
            time.sleep(10)
        else: print("TIMEOUT")
    elif c == "api":
        m = sys.argv[2]; p = sys.argv[3]; d = json.loads(sys.argv[4]) if len(sys.argv)>4 else None
        print(json.dumps(api(p, d, method=m))[:6000])
