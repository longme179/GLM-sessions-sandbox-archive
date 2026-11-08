#!/usr/bin/env python3
"""Read an OpenCode agent session: progress narration, tool trace, final report.

Message model (gateway, discovered 2026-11):
  - GET /api/session/{sid}/message returns reverse-chronological list; reverse it.
  - user messages: {type:"user", text}
  - assistant messages: {type:"assistant", content:[{type:"reasoning"|"text"|"tool-call", ...}]}
  - injected instructions (AGENTS.md etc.): {type:"synthetic", text}
  - raw shell results: {type:"shell", command, status, exit, output:{output}}
  - end of run: {type:"idle", outcome:"succeeded"|"failed"|"interrupted"}
  - agents narrate SHORT progress lines while working; the END-OF-RUN REPORT
    is the last LONG text (>= ~300 chars).

Usage:
  oc_report.py <sid> tail [-n 5]          last N assistant text lines
  oc_report.py <sid> report [--min-len 300]
  oc_report.py <sid> trace [-n 15]        last N tool calls
  oc_report.py <sid> wait [--max-min 30] [--poll 20s]   block until idle, then print report
Env: OC_URL, OC_AUTH
"""
import base64
import json
import os
import sys
import time
import urllib.request


def _call(path, timeout=90):
    req = urllib.request.Request(os.environ["OC_URL"] + path)
    req.add_header("Authorization",
                   "Basic " + base64.b64encode(os.environ["OC_AUTH"].encode()).decode())
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())["data"]


def messages(sid, take=None):
    path = f"/api/session/{sid}/message" + (f"?take={take}" if take else "")
    return list(reversed(_call(path)))  # chronological


def assistant_texts(msgs):
    out = []
    for m in msgs:
        if m.get("type") != "assistant":
            continue
        c = m.get("content")
        txt = "".join(p.get("text", "") for p in (c if isinstance(c, list) else [])
                      if p.get("type") == "text")
        if txt.strip():
            out.append(txt)
    return out


def tool_calls(msgs):
    out = []
    for m in msgs:
        if m.get("type") != "assistant":
            continue
        for p in (m.get("content") or [] if isinstance(m.get("content"), list) else []):
            if p.get("type") in ("tool-call", "tool"):
                name = p.get("name") or p.get("tool") or "?"
                state = p.get("state") if isinstance(p.get("state"), dict) else {}
                inp = p.get("input") or state.get("input") or {}
                try:
                    args = json.dumps(inp, ensure_ascii=False)[:250]
                except TypeError:
                    args = str(inp)[:250]
                out.append(f"{name} {args}")
    return out


def final_report(msgs, min_len=300):
    for t in reversed(assistant_texts(msgs)):
        if len(t) >= min_len:
            return t
    return None


def idle_outcome(msgs):
    for m in reversed(msgs):
        if m.get("type") == "idle":
            return m.get("outcome")
    return None


def main():
    if os.environ.get("OC_URL") is None or os.environ.get("OC_AUTH") is None:
        sys.exit("ERROR: export OC_URL and OC_AUTH (see tools/README.md)")
    sid = sys.argv[1]
    cmd = sys.argv[2] if len(sys.argv) > 2 else "tail"

    def argval(flag, default=None, cast=str):
        return cast(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default

    if cmd == "tail":
        msgs = messages(sid)
        for t in assistant_texts(msgs)[-argval("-n", 5, int):]:
            print("---")
            print(t[:1200])
    elif cmd == "report":
        msgs = messages(sid)
        r = final_report(msgs, argval("--min-len", 300, int))
        print(r if r else "NO REPORT YET (last texts: %r)" % assistant_texts(msgs)[-2:])
    elif cmd == "trace":
        msgs = messages(sid)
        for t in tool_calls(msgs)[-argval("-n", 15, int):]:
            print(t)
    elif cmd == "wait":
        max_min = argval("--max-min", 30, int)
        poll_s = argval("--poll", 20, int)
        deadline = time.time() + max_min * 60
        last_n = 0
        while time.time() < deadline:
            msgs = messages(sid)
            texts = assistant_texts(msgs)
            for t in texts[last_n:]:
                print("[progress]", t[:200].replace("\n", " | "))
            last_n = len(texts)
            out = idle_outcome(msgs)
            if out:
                print(f"=== RUN ENDED: {out} ===")
                r = final_report(msgs)
                print(r if r else "(no long report)")
                return
            time.sleep(poll_s)
        print("WAIT TIMEOUT")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
