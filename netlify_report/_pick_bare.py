# -*- coding: utf-8 -*-
"""从 openapi 全量端点中挑出裸资源 id 路径(无 site/account 归属前缀)-> 鉴权最可能只靠 id 的点"""
import yaml, re

with open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8') as f:
    spec = yaml.safe_load(f)

paths = spec.get('paths', {})
print('== 裸资源 id 路径(第一段不是 sites/accounts) ==')
for p in sorted(paths.keys()):
    first = p.strip('/').split('/')[0]
    if first in ('sites', 'accounts', 'users', 'user'):
        continue
    for m, op in paths[p].items():
        if m not in ('get', 'post', 'put', 'patch', 'delete'):
            continue
        summ = (op.get('summary') or '')[:55]
        print('%-7s %-85s | %s' % (m.upper(), p, summ))

print()
print('== 全部非 sites/accounts/users 前缀 path 的 id 参数 ==')
for p in sorted(paths.keys()):
    first = p.strip('/').split('/')[0]
    if first in ('sites', 'accounts', 'users', 'user'):
        continue
    ids = re.findall(r'\{([^}]+)\}', p)
    if ids:
        print('%-90s ids=%s' % (p, ids))
