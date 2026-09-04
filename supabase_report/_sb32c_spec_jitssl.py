# -*- coding: utf-8 -*-
"""提取 jit-access + ssl-enforcement 路径的完整 OpenAPI 定义"""
import json, os

d = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(d, '_sb16_openapi.json'), encoding='utf-8'))

out = []
for p in sorted(spec['paths']):
    pl = p.lower()
    if 'jit' in pl or 'ssl' in pl:
        out.append('### %s' % p)
        out.append(json.dumps(spec['paths'][p], ensure_ascii=False, indent=1))
open(os.path.join(d, '_sb32c_spec_jitssl.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
