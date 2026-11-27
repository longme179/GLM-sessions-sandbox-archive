#!/usr/bin/env python3
"""What did the simulated S2 records keep?   Usage: ghost_peek.py <simulated run dir>"""
import json
import sys

run = sys.argv[1]
data = json.load(open(f"{run}/records.json"))
records = data["records"]
print("top-level keys:", sorted(data), "| records:", len(records), "| simulated:", data.get("simulated"), "| faults:", data.get("faults"))
print("problems:", data.get("problems"))
known = {"rep", "variant", "ok", "failed_checks", "host", "settle_ms", "first_frame_ms", "close_recovery", "toast_seen", "clicks"}
for rec in records:
    if rec.get("scenario") != "s2":
        continue
    print({k: rec.get(k) for k in known - {"clicks"}})
    print("   clicks:", rec.get("clicks"))
    print("   other keys:", sorted(set(rec) - known - {"scenario"}))
summary = json.load(open(f"{run}/summary.json"))
print("summary s2:", json.dumps(summary.get("s2"))[:1600])
