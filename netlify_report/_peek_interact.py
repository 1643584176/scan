# -*- coding: utf-8 -*-
# _peek_interact.py - find interaction/agent_runner endpoints in net_lib.js
import re
src = open(r"D:\scan\netlify_report\_js\net_lib.js", encoding="utf-8", errors="replace").read()
for m in re.finditer(r'this\.request\([^)]*\)', src):
    seg = m.group(0)
    if "interaction" in seg.lower() or "agent_runner" in seg.lower() or "session" in seg.lower():
        print(seg[:300])
print("---- broader context ----")
for m in re.finditer(r'.{150}(?:interaction|agent_runner).{250}', src):
    print(repr(m.group(0)[:450]))
