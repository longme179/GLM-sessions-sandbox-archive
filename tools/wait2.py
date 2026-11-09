#!/usr/bin/env python3
"""Wait for the run that follows the LAST user prompt to reach idle.

Usage: wait2.py <sid> [--max-min 9] [--poll 20]
Differs from oc_report.py wait: only counts idle messages that appear AFTER
the last user message, so stale idles from earlier runs don't trigger return.
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


def main():
    sid = sys.argv[1]
    max_min, poll_s = 9, 20
    if "--max-min" in sys.argv:
        max_min = int(sys.argv[sys.argv.index("--max-min") + 1])
    if "--poll" in sys.argv:
        poll_s = int(sys.argv[sys.argv.index("--poll") + 1])

    def argval(flag, default, cast):
        return cast(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default

    max_min = argval("--max-min", 9, int)
    poll_s = argval("--poll", 20, int)

    deadline = time.time() + max_min * 60
    seen_texts = 0
    while time.time() < deadline:
        msgs = list(reversed(_call(f"/api/session/{sid}/message")))
        last_user = max((i for i, m in enumerate(msgs) if m.get("type") == "user"), default=0)
        idles_after = [m for m in msgs[last_user:] if m.get("type") == "idle"]
        texts = []
        for m in msgs[last_user:]:
            if m.get("type") != "assistant":
                continue
            c = m.get("content")
            txt = "".join(p.get("text", "") for p in (c if isinstance(c, list) else [])
                          if p.get("type") == "text")
            if txt.strip():
                texts.append(txt)
        for t in texts[seen_texts:]:
            print("[progress]", t[:200].replace("\n", " | "))
        seen_texts = max(seen_texts, len(texts))
        if idles_after:
            print(f"=== RUN ENDED: {idles_after[-1].get('outcome')} ===")
            long = [t for t in texts if len(t) >= 300]
            print(long[-1] if long else "(no long report)")
            return
        time.sleep(poll_s)
    print("WAIT2 TIMEOUT (run still active)")


if __name__ == "__main__":
    main()
