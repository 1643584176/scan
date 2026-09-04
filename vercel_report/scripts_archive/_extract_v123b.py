# -*- coding: utf-8 -*-
"""查看 v123 guest 日志"""
import re, io, sys

sys.stdout.reconfigure(encoding='utf-8')
txt = io.open('_run_v123_out.txt', encoding='utf-8', errors='replace').read()
seen = set()
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    for l in d.splitlines():
        s = l.strip()
        if s not in seen:
            seen.add(s)
            print(s[:400])
