# -*- coding: utf-8 -*-
"""解析 v114 结果"""
import re, io

txt = io.open('_run_v114_out.txt', encoding='utf-8', errors='replace').read()
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    chunks.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(chunks)
lines = []
for l in blob.splitlines():
    s = l.strip()
    if any(k in s for k in ('cid=', 'START', 'EXEC', 'new pids', 'pid ', 'MAIN', 'KILL', '=== P', 'V114C_DONE')):
        lines.append(s)
seen = set()
for l in lines:
    if l not in seen:
        seen.add(l)
        print(l[:360])
