# -*- coding: utf-8 -*-
"""提取 v102/v103 输出中 sandbox.Controller 相关的完整字符串"""
import re, io

for fn in ['_run_v102_out.txt', '_run_v103_out.txt']:
    print('=' * 20, fn)
    try:
        txt = io.open(fn, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    chunks = []
    for m in re.finditer(r'"data":"((?:[^"\\]|\\.)*)"', txt):
        chunks.append(m.group(1).encode().decode('unicode_escape', errors='replace'))
    blob = '\n'.join(chunks)
    seen = set()
    for ln in blob.splitlines():
        s = ln.strip()
        if 'Controller' in s or '23456' in s or '.proto' in s:
            if s not in seen:
                seen.add(s)
                print(s[:300])
    print('---- unique lines:', len(seen))
