#!/usr/bin/env python3
"""Session-scoped remote shell helper for the OpenCode gateway (tag-based).

Usage:
  oc.py new  [directory]                 create a session, print its id
  oc.py run  "command" [max_wait_sec]    run command, wait, print output
  oc.py bg   "command" "/remote/logfile" launch long job with nohup
  oc.py poll "/remote/logfile" [max_wait] poll logfile until OCJOB_DONE

Env: OC_URL (https://host), OC_AUTH (user:pass), OC_SID (session id;
     "new" prints one to export). Credentials are never hardcoded here.
"""
import base64
import json
import os
import shlex
import sys
import time
import urllib.request


def _auth():
    url = os.environ.get("OC_URL")
    auth = os.environ.get("OC_AUTH")
    if not url or not auth:
        sys.exit("ERROR: export OC_URL and OC_AUTH (see tools/README.md)")
    hdr = "Basic " + base64.b64encode(auth.encode()).decode()
    return url, {"Authorization": hdr, "Content-Type": "application/json"}


def api(path, data=None, timeout=60):
    url, headers = _auth()
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url + path, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else None


def sid():
    s = os.environ.get("OC_SID")
    if not s:
        sys.exit("ERROR: export OC_SID (or run `oc.py new` to create one)")
    return s


def new_session(directory="/home/kimhoanglong"):
    return api("/api/session", {"location": {"directory": directory}})["data"]["id"]


def messages():
    return api(f"/api/session/{sid()}/message")["data"]


def post_shell(cmd):
    api(f"/api/session/{sid()}/shell", {"command": cmd})


def wait_tag(tag, max_wait):
    deadline = time.time() + max_wait
    while time.time() < deadline:
        time.sleep(3)
        for m in messages():
            if m.get("type") == "shell" and tag in (m.get("command") or ""):
                if m.get("status") == "exited":
                    out = (m.get("output") or {}).get("output", "")
                    lines = out.split("\n")
                    if lines and lines[0].strip() == tag:
                        lines = lines[1:]
                    return m.get("exit"), "\n".join(lines)
    return -1, f"TIMEOUT after {max_wait}s"


def run(cmd, max_wait=120, quiet=False):
    tag = f"OCTAG{int(time.time() * 1000)}"
    post_shell(f"echo {tag}; {{ {cmd} ; }}")
    rc, out = wait_tag(tag, max_wait)
    if not quiet:
        print(f"exit={rc}")
        print(out)
    return rc, out


def bg(cmd, logfile):
    inner = f"{{ {cmd} ; }}; echo OCJOB_EXIT=$?; echo OCJOB_DONE"
    launcher = (f"nohup bash -c {shlex.quote(inner)} > {shlex.quote(logfile)} 2>&1 & echo BG_LAUNCHED")
    tag = f"OCTAG{int(time.time() * 1000)}"
    post_shell(f"echo {tag}; {launcher}")
    rc, out = wait_tag(tag, 30)
    print(f"exit={rc}")
    print(out)
    return rc


def poll(logfile, max_wait=600, interval=8):
    deadline = time.time() + max_wait
    while time.time() < deadline:
        time.sleep(interval)
        rc, out = run(f"tail -c 6000 {shlex.quote(logfile)}", 30, quiet=True)
        if rc != 0:
            print(out)
            return 1
        if "OCJOB_DONE" in out:
            _, out2 = run(f"grep -h OCJOB_EXIT {shlex.quote(logfile)}", 30, quiet=True)
            print("=== job status ===")
            print(out2)
            print("=== last log lines ===")
            print(out)
            return 0 if "OCJOB_EXIT=0" in out2 else 1
    print(f"POLL TIMEOUT after {max_wait}s", file=sys.stderr)
    return -1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "new":
        print(new_session(sys.argv[2] if len(sys.argv) > 2 else "/home/kimhoanglong"))
    elif mode == "run":
        rc, _ = run(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 120)
        sys.exit(0 if rc == 0 else 1)
    elif mode == "bg":
        sys.exit(0 if bg(sys.argv[2], sys.argv[3]) == 0 else 1)
    elif mode == "poll":
        sys.exit(0 if poll(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 600) == 0 else 1)
    else:
        print(__doc__)
        sys.exit(1)
