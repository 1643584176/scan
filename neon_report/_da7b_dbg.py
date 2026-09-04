# -*- coding: utf-8 -*-
"""调试:打印 spec paths 中 auth 路径 key 样本"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec.get('paths', {})
print('type:', type(paths).__name__)
ks = list(paths.keys())
print('sample keys:')
for k in ks:
    if 'auth' in k or 'data-api' in k or k == '/projects':
        print(' ', repr(k))
