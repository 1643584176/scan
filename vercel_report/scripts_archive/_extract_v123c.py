# -*- coding: utf-8 -*-
"""v123 日志尾部"""
import re, io, sys

sys.stdout.reconfigure(encoding='utf-8')
txt = io.open('_run_v123_out.txt', encoding='utf-8', errors='replace').read()
lines = []
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    for l in d.splitlines():
        lines.append(l.strip())
seen = set()
uniq = [l for l in lines if not (l in seen or seen.add(l))]
for l in uniq[-40:]:
    print(l[:300])
