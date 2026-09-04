# -*- coding: utf-8 -*-
"""解析 v105 输出"""
import re, io

txt = io.open('_run_v105_out.txt', encoding='utf-8', errors='replace').read()
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    chunks.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(chunks)
print('total chars:', len(blob))
lines = [l for l in blob.splitlines() if l.startswith('[') or l.startswith('GRPC') or '=== P' in l or 'candidates' in l]
for l in lines:
    print(l[:200])
