# -*- coding: utf-8 -*-
"""解析 v119 结果"""
import re, io, sys

sys.stdout.reconfigure(encoding='utf-8')
txt = io.open('_run_v119_out.txt', encoding='utf-8', errors='replace').read()
keys = ('cid=', 'START', 'EXEC', 'processId', 'STREAM', 'C1', 'C2', 'WAIT', 'KILL',
        '=== P', 'V119C_DONE')
seen = set()
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    for l in d.splitlines():
        st = l.strip()
        if any(k in st for k in keys) and st not in seen:
            seen.add(st)
            print(st[:600])
