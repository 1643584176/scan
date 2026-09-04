# -*- coding: utf-8 -*-
"""解析 v121 结果"""
import re, io, sys

sys.stdout.reconfigure(encoding='utf-8')
txt = io.open('_run_v121_out.txt', encoding='utf-8', errors='replace').read()
keys = ('cid=', 'START', 'EXEC', 'processId', 'SO1', 'SO2', 'SO3', 'GOT', 'KILL', '=== P', 'V121C_DONE')
seen = set()
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    for l in d.splitlines():
        st = l.strip()
        if any(k in st for k in keys) and st not in seen:
            seen.add(st)
            print(st[:700])
