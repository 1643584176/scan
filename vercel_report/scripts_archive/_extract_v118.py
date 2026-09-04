# -*- coding: utf-8 -*-
"""解析 v118 结果: 提取关键日志行"""
import re, io, sys

sys.stdout.reconfigure(encoding='utf-8')
txt = io.open('_run_v118_out.txt', encoding='utf-8', errors='replace').read()
keys = ('cid=', 'START', 'EXEC', 'processId', 'STREAM', 'OUT', 'WAIT', 'KILL',
        '=== P', 'V118C_DONE', 'STREAMOUT')
seen = set()
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    for l in d.splitlines():
        st = l.strip()
        if any(k in st for k in keys) and st not in seen:
            seen.add(st)
            print(st[:600])
