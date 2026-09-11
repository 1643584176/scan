# -*- coding: utf-8 -*-
"""1) 打印 r13x-r16x + r197 各脚本头部注释(设计叙述) 2) 搜索经验库 keyset/游标 沉淀"""
import os, io, re

DIR = r'D:/scan/figma_report'
print('=' * 20, 'rounds r129-r165 design notes')
for fn in sorted(os.listdir(DIR)):
    if not fn.endswith('.py'):
        continue
    m = re.match(r'_figma_r1(2[9]|3\d|4\d|5\d|6\d|97)', fn)
    if not m:
        continue
    txt = io.open(os.path.join(DIR, fn), encoding='utf-8', errors='ignore').read()
    lines = [ln.strip() for ln in txt.split('\n')[:6] if ln.strip().startswith('#')]
    note = ' | '.join(l.lstrip('# ').strip() for l in lines[:3])
    print('%-30s %s' % (fn, note[:150]))

print()
print('=' * 20, 'search 经验库 for keyset/cursor')
DIR2 = r'D:/scan/经验/全局经验/SQL注入经验库'
for fn in sorted(os.listdir(DIR2)):
    if not fn.endswith('.md'):
        continue
    txt = io.open(os.path.join(DIR2, fn), encoding='utf-8', errors='ignore').read()
    for kw in ['keyset', '游标', 'µs', 'tie-break', 'versions', 'OR 型']:
        cnt = len(re.findall(re.escape(kw), txt))
        if cnt:
            print('%-28s %-10s x%d' % (fn, kw, cnt))
