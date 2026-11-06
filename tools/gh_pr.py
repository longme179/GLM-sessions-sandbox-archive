#!/usr/bin/env python3
"""Create (and optionally immediately merge) a GitHub PR via the REST API.

Token is read from --token-file (default /tmp/.ghtoken) — a runtime-only file
that must never be committed anywhere.

Usage:
  gh_pr.py --repo owner/name --head branch --title "..." --body-file BODY.md
          [--base main] [--token-file /tmp/.ghtoken] [--merge] [--merge-msg "..."]
"""
import argparse
import json
import sys
import urllib.request

p = argparse.ArgumentParser()
p.add_argument("--repo", required=True)
p.add_argument("--head", required=True)
p.add_argument("--base", default="main")
p.add_argument("--title", required=True)
p.add_argument("--body-file", default=None)
p.add_argument("--body", default=None)
p.add_argument("--token-file", default="/tmp/.ghtoken")
p.add_argument("--merge", action="store_true")
p.add_argument("--merge-msg", default="")
args = p.parse_args()

TOKEN = open(args.token_file).read().strip()
API = f"https://api.github.com/repos/{args.repo}"
body = open(args.body_file).read() if args.body_file else (args.body or "")


def call(path, data=None, method=None):
    hdr = {"Authorization": f"token {TOKEN}",
           "Accept": "application/vnd.github+json",
           "Content-Type": "application/json"}
    req = urllib.request.Request(API + path, data=json.dumps(data).encode() if data is not None else None,
                                 method=method, headers=hdr)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else None


pr = call("/pulls", {
    "title": args.title,
    "head": args.head,
    "base": args.base,
    "body": body,
})
print("PR created:", pr["number"], pr["html_url"])

if args.merge:
    merge = call(f"/pulls/{pr['number']}/merge", {
        "merge_method": "merge",
        "commit_title": f"Merge pull request #{pr['number']} from {args.repo.split('/')[0]}/{args.head}",
        "commit_message": args.merge_msg or args.title,
    }, method="PUT")
    print("Merge:", json.dumps(merge))
