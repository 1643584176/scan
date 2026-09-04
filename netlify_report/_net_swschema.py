# -*- coding: utf-8 -*-
"""Netlify:查 Deploy schema 定义"""
import yaml

sw = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))

def dump_schema(name, depth=0, seen=None):
    if seen is None:
        seen = set()
    if name in seen or depth > 3:
        return
    seen.add(name)
    s = sw['definitions'].get(name)
    if not s:
        return
    print('  ' * depth + '=== %s ===' % name)
    if 'properties' in s:
        for k, v in s['properties'].items():
            t = v.get('type') or v.get('$ref', '?')
            print('  ' * depth + '  %s: %s %s' % (k, t, '(required)' if k in (s.get('required') or []) else ''))
            if '$ref' in v:
                dump_schema(v['$ref'].split('/')[-1], depth + 1, seen)
    elif '$ref' in s:
        dump_schema(s['$ref'].split('/')[-1], depth, seen)

dump_schema('Deploy')
