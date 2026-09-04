# -*- coding: utf-8 -*-
"""找 API base URL 定义(api.netlify.com / /api/v1 拼接处)+ 所有 "/xxx".concat 模式路径"""
import re, os

d = r'D:\scan\netlify_report\_js'
for fn in os.listdir(d):
    if not fn.endswith('.js'):
        continue
    data = open(os.path.join(d, fn), encoding='utf-8', errors='ignore').read()
    if 'api.netlify.com' in data or 'api/v1' in data:
        hits = [m.start() for m in re.finditer(r'api\.netlify\.com|api/v1', data)]
        print('==', fn, len(hits))
        for i in hits[:4]:
            print('  ...%s...' % data[max(0, i - 150):i + 150].replace('\n', ' '))
            print()
