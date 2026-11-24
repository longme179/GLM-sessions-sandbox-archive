#!/usr/bin/env python3
"""Agent-2 file transfer over the OpenCode PTY (base64-safe, byte-exact).
Usage:
  python3 hostfile.py fetch <host_abs_path> <local_path>
  python3 hostfile.py push  <local_path> <host_abs_path>
"""
import sys, re, json, time, base64
import websocket, urllib.request

SERVER_URL = "https://eceb57eda0919593.x3v7ggvsseh7.opentunnel.xyz"
USER, PASSWORD = "opencode", "gx1EGSesZZWUAF5I4gEY6v_eNH1yfsFIqfT8qLMwlrg"

ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[()][0-9A-B]|\r")

def auth():
    return "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()

def run(cwd, cmd, timeout=120):
    """Run cmd in a fresh PTY (cwd applied), return clean text output."""
    req = urllib.request.Request(SERVER_URL + "/api/pty", method="POST",
        data=json.dumps({"directory": cwd}).encode(),
        headers={"Content-Type": "application/json", "Authorization": auth()})
    with urllib.request.urlopen(req, timeout=20) as r:
        pty_id = json.load(r)["data"]["id"]
    try:
        ws = websocket.create_connection(
            SERVER_URL.replace("https://", "wss://") + f"/api/pty/{pty_id}/connect",
            timeout=15, header={"Authorization": auth()})
        marker = f"M{int(time.time()*1000)%999999}"
        ws.send("export PS1='>' PROMPT_COMMAND=''\n" + cmd + f"\nprintf '%s' '{marker}RC$?'\n")
        out, deadline = [], time.time() + timeout
        rc = None
        while time.time() < deadline:
            ws.settimeout(max(1, deadline - time.time()))
            try:
                frame = ws.recv()
            except Exception:
                break
            if isinstance(frame, bytes):
                frame = frame.decode("utf-8", "replace")
            if not isinstance(frame, str):
                continue
            out.append(frame)
            m = re.search(re.escape(marker) + r"RC(\d+)", ANSI.sub("", frame))
            if m:
                rc = int(m.group(1))
                # drain briefly
                end = time.time() + 0.6
                while time.time() < end:
                    try:
                        ws.settimeout(0.3)
                        extra = ws.recv()
                        if isinstance(extra, bytes):
                            extra = extra.decode("utf-8", "replace")
                        if isinstance(extra, str):
                            out.append(extra)
                    except Exception:
                        break
                break
        ws.close()
    finally:
        try:
            urllib.request.urlopen(urllib.request.Request(
                f"{SERVER_URL}/api/pty/{pty_id}", method="DELETE",
                headers={"Authorization": auth()}), timeout=10)
        except Exception:
            pass
    clean = ANSI.sub("", "".join(out))
    # strip the echoed command block (everything up to the first \n after our command echo)
    return clean, rc

def fetch(host_path, local_path):
    text, rc = run("/", f"base64 -w0 {host_path}", timeout=180)
    m = re.findall(r"[A-Za-z0-9+/=]{500,}", text)
    if not m:
        raise RuntimeError(f"no payload found (rc={rc}); head={text[:300]!r}")
    payload = max(m, key=len)
    data = base64.b64decode(payload)
    open(local_path, "wb").write(data)
    return len(data)

def push(local_path, host_path):
    data = open(local_path, "rb").read()
    b64 = base64.b64encode(data).decode()
    # write in one heredoc-free way: printf the base64 then decode
    cmd = (f"printf '%s' '{b64}' | base64 -d > {host_path} && "
           f"echo PUSHED $(wc -c < {host_path})")
    text, rc = run("/", cmd, timeout=180)
    if "PUSHED " + str(len(data)) not in text:
        raise RuntimeError(f"push verify failed (rc={rc}): {text[-200:]!r}")
    return len(data)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "fetch":
        print("fetched", fetch(sys.argv[2], sys.argv[3]), "bytes")
    elif mode == "push":
        print("pushed", push(sys.argv[2], sys.argv[3]), "bytes")
    else:
        raise SystemExit("mode must be fetch|push")
