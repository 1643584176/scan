# -*- coding: utf-8 -*-
"""提取 9300 chunk 的 privacyMode 判定函数完整上下文 + 各 chunk privacyMode 用法"""
import os, re

JS = r'F:/scan/figma_report/_js'

def ctx_of(fn, anchor, before=700, after=700, limit=4):
    p = os.path.join(JS, fn)
    c = open(p, encoding='utf-8', errors='ignore').read()
    print('#' * 20, fn, f'({len(c)} bytes)')
    idx = 0
    n = 0
    while n < limit:
        i = c.find(anchor, idx)
        if i < 0:
            break
        print(f'--- anchor@{i} ---')
        print(c[max(0, i - before):i + after].replace('\n', ' '))
        print()
        idx = i + 1
        n += 1

ctx_of('9300-41a18cb0f8ba922b.min.js', 'privacyMode===l.YD.FILE', 900, 600)
ctx_of('0c62c2fd-d032e3933f62f517.min.js', 'privacyMode:"user"', 500, 400)
ctx_of('8049-7a9832b7849f38f7.min.js', 'privacyMode:"file"', 400, 300)
ctx_of('2688-74090ce86ecdf35c.min.js', '?.privacyMode', 500, 300)
