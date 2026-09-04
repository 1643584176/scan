# -*- coding: utf-8 -*-
"""v106 完整输出检查"""
import re, io

txt = io.open('_run_v106_out.txt', encoding='utf-8', errors='replace').read()
chunks = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    chunks.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
blob = '\n'.join(chunks)
print('total chars:', len(blob))
print(blob[:6000])
