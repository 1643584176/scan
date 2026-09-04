# -*- coding: utf-8 -*-
"""api-create.services.netlify.com 调用上下文"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()
for key in ['api-create.services.netlify.com', 'identeer.services.netlify.com']:
    print('=' * 80)
    for m in re.finditer(re.escape(key), data):
        s = max(0, m.start() - 700)
        e = min(len(data), m.end() + 700)
        print(data[s:e].replace('\n', ' '))
        print('-' * 70)
        break
