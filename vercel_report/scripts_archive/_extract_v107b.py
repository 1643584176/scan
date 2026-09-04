# -*- coding: utf-8 -*-
"""解析 v107 结果 (修正前缀)"""
import re, io

txt = io.open('_run_v107_out.txt', encoding='utf-8', errors='replace').read()
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    chunks.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(chunks)
lines = []
for l in blob.splitlines():
    s = l.strip()
    if any(k in s for k in ('CONN cell', 'CONN metric', 'CONN apm', 'GRPC cell', 'Store/', 'Controller/', 'rt.Sandbox',
                            'HTTP ', '=== P', 'V107C_DONE')):
        lines.append(s)
seen = set()
for l in lines:
    if l not in seen:
        seen.add(l)
        print(l[:300])
