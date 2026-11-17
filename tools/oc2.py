#!/usr/bin/env python3
"""Agent-2 orchestration bridge to the OpenCode gateway (agent-1 session).

Env: OC_URL, OC_AUTH (user:pass), OC_SID (agent-1 session id).

Commands:
  status                     session summary (id, title, busy/idle, outcome)
  sh "cmd" [timeout_s]       global agent-free shell (POST /api/shell + output paging)
  dispatch <prompt_file> [wait_s]   send prompt to OC_SID, wait for idle, print final text
  wait [wait_s]              block until session idle
  last [n] [max_chars]       print last n messages' text, chronological
  put <local> <remote>       byte-exact upload (base64 chunks, md5-gated)
"""
import base64, hashlib, json, os, sys, time, urllib.request, urllib.error

URL = os.environ["OC_URL"].rstrip("/")
SID = os.environ.get("OC_SID", "")
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
    r = api("/api/shell", {"command": cmd, "timeout": int(wait * 1000)})
    if not r or "__http_error" in r:
        return f"SUBMIT-FAIL {r}"
    d = r.get("data", r)
    jid = d.get("id") if isinstance(d, dict) else None
    if not jid:
        return f"NO-JOB-ID {r}"
    out, cursor, deadline = [], 0, time.time() + wait + 45
    while time.time() < deadline:
        o = api(f"/api/shell/{jid}/output?cursor={cursor}&limit=2000000")
        if o:
            dd = o.get("data", o) or {}
            chunk = dd.get("output") or dd.get("text") or ""
            if chunk:
                out.append(chunk)
            nc = dd.get("cursor")
            if isinstance(nc, int):
                cursor = nc
        st = api(f"/api/shell/{jid}")
        s = (st or {}).get("data", st) or {}
        status = s.get("status")
        if status in ("done", "error", "exited", "completed", "failed"):
            o = api(f"/api/shell/{jid}/output?cursor={cursor}&limit=2000000")
            if o:
                dd = o.get("data", o) or {}
                out.append(dd.get("output") or dd.get("text") or "")
            tail = f"\n[status={status} exit={s.get('exitCode', s.get('exit'))}]" if status not in ("done", "completed") else ""
            return "".join(out) + tail
        time.sleep(2)
    return "".join(out) + "\n[TIMEOUT]"


def sess_info():
    r = api(f"/api/session/{SID}")
    return (r or {}).get("data", r) or {}


def wait_idle(wait_s=600):
    dl = time.time() + wait_s
    while time.time() < dl:
        s = sess_info()
        tm = s.get("time", {})
        if tm.get("idle") and (not tm.get("busy") or tm["idle"] > tm["busy"]):
            return f"IDLE outcome={s.get('outcome')}"
        time.sleep(10)
    return "TIMEOUT"


def msgs(n=None):
    r = api(f"/api/session/{SID}/message")
    d = (r or {}).get("data", r)
    if isinstance(d, dict):
        d = d.get("messages", [])
    d = list(reversed(d))  # chronological
    return d[-n:] if n else d


def text_of(m):
    for key in ("content", "parts"):
        parts = m.get(key) or []
        if parts and isinstance(parts, list):
            return "\n".join(p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text")
    return m.get("text") or ""


def put(local, remote):
    data = open(local, "rb").read()
    md5 = hashlib.md5(data).hexdigest()
    sh(f"mkdir -p $(dirname {remote})")
    # first chunk truncates
    for i in range(0, len(data), 30000) if data else [0]:
        chunk = data[i:i + 30000]
        b64 = base64.b64encode(chunk).decode()
        op = ">" if i == 0 else ">>"
        r = sh(f"printf %s {b64} | base64 -d {op} {remote}", 60)
        if "status=error" in r or "SUBMIT-FAIL" in r:
            return f"CHUNK-FAIL at {i}: {r[:300]}"
    got = sh(f"md5sum {remote} 2>/dev/null | cut -d' ' -f1; wc -c < {remote}", 60).strip().split()
    if len(got) >= 2 and got[0] == md5 and int(got[1]) == len(data):
        return f"OK {len(data)} bytes md5={md5}"
    return f"MISMATCH local={len(data)}/{md5} remote={got}"


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "status":
        s = sess_info()
        tm = s.get("time", {})
        print(json.dumps({"id": s.get("id"), "title": s.get("title"), "model": s.get("model"),
                          "outcome": s.get("outcome"),
                          "busy": tm.get("busy"), "idle": tm.get("idle"),
                          "dir": s.get("location", {}).get("directory")}, indent=1))
    elif c == "sh":
        print(sh(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 120))
    elif c == "dispatch":
        pf = sys.argv[2]
        ws = int(sys.argv[3]) if len(sys.argv) > 3 else 600
        r = api(f"/api/session/{SID}/prompt", {"text": open(pf).read()}, timeout=180)
        if not r or "__http_error" in r:
            print("PROMPT-FAIL", json.dumps(r)[:500]); sys.exit(1)
        print("PROMPT-SENT", json.dumps(r)[:200])
        print(wait_idle(ws))
        # final assistant text = last assistant message with text content
        final = ""
        for m in reversed(msgs(30)):
            if m.get("type") == "assistant":
                t = text_of(m)
                if t.strip():
                    final = t
                    break
        print("=== FINAL ASSISTANT TEXT ===")
        print(final)
    elif c == "wait":
        print(wait_idle(int(sys.argv[2]) if len(sys.argv) > 2 else 600))
    elif c == "last":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        mc = int(sys.argv[3]) if len(sys.argv) > 3 else 4000
        for m in msgs(n):
            t = text_of(m) or (m.get("type", "") + " " + json.dumps({k: v for k, v in m.items() if k in ("outcome", "id")})[:200])
            print(f"--- {m.get('type', m.get('role'))} {m.get('id', '')[:24]} ---")
            print(t[:mc])
    elif c == "put":
        print(put(sys.argv[2], sys.argv[3]))
    else:
        print(__doc__)
