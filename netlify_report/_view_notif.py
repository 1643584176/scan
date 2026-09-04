# -*- coding: utf-8 -*-
"""查 swagger: notification 相关 path + site 创建/更新 schema 里的 notification 字段"""
import yaml

spec = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
paths = spec['paths']

print('=== notification/webhook 相关 path ===')
for p in sorted(paths.keys()):
    if any(k in p.lower() for k in ['notif', 'webhook', 'hook']):
        print(' ', p, '->', [m for m in paths[p] if m in ('get', 'post', 'put', 'patch', 'delete')])

print()
print('=== Site 相关 schema 中 notification 字段 ===')
schs = spec.get('components', {}).get('schemas', {})
for n, d in schs.items():
    props = d.get('properties', {})
    for pn in props:
        if 'notif' in pn.lower() or 'webhook' in pn.lower() or 'notification' in pn.lower():
            print('schema %s prop %s:' % (n, pn), json.dumps(props[pn])[:200])
