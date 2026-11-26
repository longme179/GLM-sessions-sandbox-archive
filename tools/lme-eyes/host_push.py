#!/usr/bin/env python3
"""Push a file to the host through the PTY bridge in line-sized chunks.

The bridge sends the whole command as one websocket frame; a 11 KB line worked but a
22 KB one hung the PTY, so everything travels as <=3 KB base64 lines that each
decode-and-append inside a quoted heredoc body.  Usage:

    python3 host_push.py <local_file> <remote_path>
"""
import base64
import sys
import time

sys.path.insert(0, "/home/z/my-project/scripts")
from host_run import run  # noqa: E402

CHUNK = 3000          # base64 chars per line — safely under the observed hang threshold


def push(local: str, remote: str, timeout: int = 60) -> int:
    data = base64.b64encode(open(local, "rb").read()).decode()
    remote_dir = remote.rsplit("/", 1)[0]
    lines = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
    # One open() per line keeps every bridge command short; -n stops echo mangling blanks.
    for n, line in enumerate(lines):
        cmd = (f"mkdir -p '{remote_dir}' && printf '%s' '{line}' >> /tmp/.push_b64 && "
               f"echo pushed {n + 1}/{len(lines)}")
        rc, text = run(cmd, timeout, "/")
        if rc != 0:
            print(f"chunk {n + 1}/{len(lines)} failed rc={rc}: {text[-200:]}")
            return 1
        time.sleep(0.05)
    rc, text = run(f"base64 -d /tmp/.push_b64 > '{remote}' && rm -f /tmp/.push_b64 && "
                   f"cmp -s <(base64 -w0 '{remote}') <(printf '%s' '{data[:CHUNK]}') ; "
                   f"wc -c < '{remote}'", timeout, "/")
    print(text[-300:])
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(push(sys.argv[1], sys.argv[2]))
