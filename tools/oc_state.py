#!/usr/bin/env python3
"""Correct run-state check: idle counts only if it appears AFTER the last
user message. Prints: state, message count, last 3 tool calls."""
import os
import sys

sys.path.insert(0, '/home/z/my-project/scripts')
import oc_report

msgs = oc_report.messages(os.environ['OC_SID'])
last_user = max((i for i, m in enumerate(msgs) if m.get('type') == 'user'), default=-1)
idle = None
for m in msgs[last_user + 1:]:
    if m.get('type') == 'idle':
        idle = m.get('outcome')
state = idle or 'working'
print(f"{state} msgs={len(msgs)}")
for t in oc_report.tool_calls(msgs)[-3:]:
    print('  tool:', t[:160])
