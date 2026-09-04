# -*- coding: utf-8 -*-
"""从 _sb16_openapi.json 提取 ssl-enforcement / jit-access 路径定义 (单行 JSON 切片)"""
import json, os

d = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(d, '_sb16_openapi.json'), encoding='utf-8'))

paths = spec.get('paths', {})
hits = [p for p in paths if 'ssl' in p.lower() or 'jit' in p.lower() or 'claim' in p.lower() or 'login-role' in p.lower()]
out = []
for p in sorted(hits):
    out.append('### %s' % p)
    out.append(json.dumps(paths[p], ensure_ascii=False, indent=1))

open(os.path.join(d, '_sb32_spec_jitssl.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out)[:6000])
