# -*- coding: utf-8 -*-
"""提取 v126 descriptor 解析结果"""
import re, io, sys

sys.stdout.reconfigure(encoding='utf-8')
txt = io.open('_run_v126_out.txt', encoding='utf-8', errors='replace').read()
blobs = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    blobs.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(blobs)
io.open('_v126d_local.txt', 'w', encoding='utf-8', errors='replace').write(blob)
lines = blob.splitlines()
print('total lines:', len(lines))
seen = set()
for l in lines:
    if any(k in l for k in ('proto names', 'parsed ', '=== FILE', 'SVC vercel.hive', 'MSG vercel.hive')):
        s = l[:250]
        if s not in seen:
            seen.add(s)
            print(s)
