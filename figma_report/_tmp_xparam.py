# -*- coding: utf-8 -*-
"""全局搜索: 跨参数/多字段/中性化/独立解析/条件消失/注释族 的既有沉淀"""
import os, io, re

ROOT = r'D:/scan/经验/全局经验/SQL注入经验库'
FIG = r'D:/scan/figma_report'
PATS = ['跨参数', '中性化', '独立解析', '条件消失', '注释族', '分片', '多字段', '多参数', '拼接', '缝合']

def scan(path, label):
    for fn in sorted(os.listdir(path)):
        if not fn.endswith('.md'):
            continue
        txt = io.open(os.path.join(path, fn), encoding='utf-8', errors='ignore').read()
        lines = txt.split('\n')
        hits = []
        for i, ln in enumerate(lines):
            for p in PATS:
                if p in ln:
                    hits.append((i + 1, p, ln.strip()[:165]))
                    break
        if hits:
            print('#' * 8, label, fn, '(%d)' % len(hits))
            for n, p, s in hits[:40]:
                print('  [%s] %4d| %s' % (p, n, s))
            print()

scan(ROOT, 'LIB')
scan(FIG, 'DOC')
