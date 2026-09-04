# -*- coding: utf-8 -*-
import re, io

txt = io.open('_run_v102_out.txt', encoding='utf-8', errors='replace').read()
seen = set()
for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
    d = m.group(1).encode().decode('unicode_escape', errors='replace')
    key = d[:60]
    if key in seen:
        continue
    seen.add(key)
    if any(k in d for k in ('vsock+0x', 'QueueSel', 'desc phys', 'desc page', 'Q0 ', 'config 0x', 'status=0x', 'mem fd', 'M3', 'M4', '--- /proc', 'RAM@', 'mknod')):
        print(d[:1500])
        print('======')
