# -*- coding: utf-8 -*-
"""jigsaw/identeer/socketeer 在 bundle 的调用上下文"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()
for key in ['jigsaw', 'socketeer', 'identeer']:
    print('=' * 80)
    print('KEY:', key)
    cnt = 0
    for m in re.finditer(re.escape(key), data):
        s = max(0, m.start() - 400)
        e = min(len(data), m.end() + 400)
        print(data[s:e].replace('\n', ' '))
        print('-' * 70)
        cnt += 1
        if cnt >= 3:
            break
