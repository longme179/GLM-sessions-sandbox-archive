#!/usr/bin/env python3
"""config/architecture.json: register the two eyes files of the harness (check.sh: "Unclassified source").

Usage: python3 arch_fix_repo.py <repo checkout>
Anchored edits only; the file must still parse as JSON afterwards."""
import json
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "config/architecture.json"
src = path.read_text()
new = ["scripts/perf/eyes.py", "scripts/perf/eyes_patch_repo.py"]


def sub(old, replacement, note):
    global src
    if replacement in src:
        print(f"  already in: {note}")
        return
    assert src.count(old) == 1, f"{note}: anchor found {src.count(old)} times"
    src = src.replace(old, replacement)
    print(f"  edited: {note}")


added = "".join(f'  "{name}",\n' for name in new)
sub('  "scripts/perf/selftest.py"\n ],\n "toolingFiles": [',
    added + '  "scripts/perf/selftest.py"\n ],\n "toolingFiles": [', "the harness file list keeps the eyes files")
sub('  "scripts/perf/selftest.py"\n ],\n "legacyEdges": [',
    added + '  "scripts/perf/selftest.py"\n ],\n "legacyEdges": [', "toolingFiles keeps the eyes files")

data = json.loads(src)
listed = [name for name in new if f'"{name}"' in src]
print("json ok; listed:", listed)
path.write_text(src)
print("written:", path)
