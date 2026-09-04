# -*- coding: utf-8 -*-
"""看 net_actions.js / net_app.js 里 verify 与 cdnTier 上下文"""
import re, sys

for fn in [r'D:\scan\netlify_report\_js\net_actions.js', r'D:\scan\netlify_report\_js\net_app.js']:
    data = open(fn, encoding='utf-8', errors='ignore').read()
    print('#' * 20, fn)
    for key, lim in [('functions/verify', 3), ('cdnTier', 4)]:
        n = 0
        for m in re.finditer(re.escape(key), data):
            s = max(0, m.start() - 700)
            e = min(len(data), m.end() + 700)
            print('=' * 30, key, 'hit', n)
            print(data[s:e].replace('\n', ' '))
            n += 1
            if n >= lim:
                break
