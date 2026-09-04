# -*- coding: utf-8 -*-
"""从 v99 输出提取 unix socket 表 (cell.sock 路径)"""
import re, io

txt = io.open('_run_v99_out.txt', encoding='utf-8', errors='replace').read()
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    chunks.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(chunks)
# 找 unix 表段
i = blob.find('H1')
seg = blob[i:i + 4000]
for ln in seg.splitlines():
    if '.sock' in ln or 'unix' in ln.lower() or 'H1' in ln:
        print(ln[:220])
