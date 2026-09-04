# -*- coding: utf-8 -*-
import re, io

txt = io.open('_run_v104_out.txt', encoding='utf-8', errors='replace').read()
# 收集所有包含 GRPC p23456 的行
lines = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    for ln in d.splitlines():
        if 'GRPC p23456' in ln or '=== P1' in ln or 'P3 celld' in ln or 'proto hits' in ln:
            lines.append(ln)
for ln in lines[:80]:
    print(ln[:300])
