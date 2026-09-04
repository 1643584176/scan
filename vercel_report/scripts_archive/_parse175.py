# -*- coding: utf-8 -*-
"""解析 _run_v175_out.txt 提取 payload 日志行"""
import json, re, sys

src = r'D:\scan\_run_v175_out.txt'
dst = r'D:\scan\_v175_view.txt'
seen = set()
out = []
for ln in open(src, encoding='utf-8', errors='replace'):
    try:
        o = json.loads(ln)
        d = o.get('data', '')
    except Exception:
        d = ln
    if not isinstance(d, str):
        continue
    for m in re.finditer(r'\[\d+\.\d\] ([^\n]+)', d):
        s = m.group(1)
        if s not in seen:
            seen.add(s)
            out.append(s[:400])
open(dst, 'w', encoding='utf-8').write('\n'.join(out))
print('lines=%d' % len(out))
