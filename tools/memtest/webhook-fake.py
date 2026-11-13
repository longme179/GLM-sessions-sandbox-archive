#!/usr/bin/env python3
"""webhook-fake.py — fake Discord webhook receiver for K1 measurement.

Accepts POST (new message) and PATCH (edit-in-place) on any path, logs each
request to ~/dev-memtest/results/webhook-fake.log, replies 200 with a JSON
body containing an "id" so the daemon can persist the message id.
Standalone tool (policy Q8): never commit into the Minewrap app repo.
"""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

LOG_PATH = os.path.expanduser(
    os.environ.get("WEBHOOK_FAKE_LOG", "~/dev-memtest/results/webhook-fake.log")
)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
LOG = open(LOG_PATH, "a", buffering=1)


class Handler(BaseHTTPRequestHandler):
    def _reply(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        LOG.write(
            "%.3f %s %s bytes=%d\n" % (time.time(), self.command, self.path, len(body))
        )
        resp = json.dumps({"id": "fake-%d" % int(time.time() * 1000)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    do_POST = _reply
    do_PATCH = _reply

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("WEBHOOK_FAKE_PORT", "9999"))
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
