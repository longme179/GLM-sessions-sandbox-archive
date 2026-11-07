#!/usr/bin/env python3
"""Send a prompt (from file) to a remote OpenCode session.

Usage: oc_prompt.py <session_id> <prompt_file>
Env: OC_URL, OC_AUTH (user:pass)
"""
import base64
import json
import os
import sys
import urllib.request


def main():
    if os.environ.get("OC_URL") is None or os.environ.get("OC_AUTH") is None:
        sys.exit("ERROR: export OC_URL and OC_AUTH (see tools/README.md)")
    sid, path = sys.argv[1], sys.argv[2]
    text = open(path).read()
    req = urllib.request.Request(os.environ["OC_URL"] + f"/api/session/{sid}/prompt", method="POST")
    req.add_header("Authorization",
                   "Basic " + base64.b64encode(os.environ["OC_AUTH"].encode()).decode())
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps({"text": text}).encode()
    with urllib.request.urlopen(req, timeout=120) as r:
        print(r.read().decode()[:400])


if __name__ == "__main__":
    main()
