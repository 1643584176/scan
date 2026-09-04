# -*- coding: utf-8 -*-
"""枚举所有 .js 中 /.netlify/functions/ 引用,去重汇总"""
import re, glob, os

fns = set()
ctx = {}
for fn in glob.glob(r'D:\scan\netlify_report\_js\*.js'):
    data = open(fn, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r'"/\.netlify/functions/([^"]+)"', data):
        p = m.group(1)
        fns.add(p)
        ctx.setdefault(p, []).append((os.path.basename(fn), m.start()))

for p in sorted(fns):
    hits = ctx[p]
    # 取第一个 hit 前后各 260 字符看调用形态
    fn, pos = hits[0]
    data = open(os.path.join(r'D:\scan\netlify_report\_js', fn), encoding='utf-8', errors='ignore').read()
    s = max(0, pos - 260)
    e = min(len(data), pos + 260)
    seg = data[s:e].replace('\n', ' ')
    print('### %-55s (%d hits)' % (p, len(hits)))
    print('    ' + seg[:400])
    print()
