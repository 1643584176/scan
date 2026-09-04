# -*- coding: utf-8 -*-
"""抽 Data API + Buckets + Credentials + Functions 的完整 schema 定义(引用解析)"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
comps = spec['components']['schemas']

def resolve(ref):
    name = ref.split('/')[-1]
    return comps.get(name, {})

def show_schema(name, depth=0, seen=None):
    seen = seen or set()
    if depth > 3 or name in seen:
        return
    seen.add(name)
    s = comps.get(name, {})
    print('%s%s:' % ('  ' * depth, name), s.get('type'), '|', (s.get('description') or '')[:80])
    if 'properties' in s:
        for pn, pv in s['properties'].items():
            req = 'REQ' if pn in s.get('required', []) else 'opt'
            if '$ref' in pv:
                print('%s  - %s (%s) -> %s' % ('  ' * depth, pn, req, pv['$ref'].split('/')[-1]))
            else:
                extra = pv.get('enum') or pv.get('default')
                print('%s  - %s (%s) %s %s %s' % ('  ' * depth, pn, req, pv.get('type'), json.dumps(extra)[:60] if extra else '', (pv.get('description') or '')[:90]))
    elif s.get('type') == 'array':
        it = s.get('items', {})
        if '$ref' in it:
            print('%s  items -> %s' % ('  ' * depth, it['$ref'].split('/')[-1]))

print('========== Data API 相关 ==========')
for n in sorted(comps):
    ln = n.lower()
    if any(k in ln for k in ['dataapi', 'data_api', 'data-api', 'query', 'table', 'sql']):
        show_schema(n)
print()
print('========== Buckets ==========')
for n in sorted(comps):
    ln = n.lower()
    if any(k in ln for k in ['bucket', 'object', 'presign', 's3']):
        show_schema(n)
print()
print('========== Credentials ==========')
for n in sorted(comps):
    ln = n.lower()
    if 'credential' in ln or ln in ('apitoken',) or 'secret' in ln:
        show_schema(n)
print()
print('========== Functions ==========')
for n in sorted(comps):
    ln = n.lower()
    if 'function' in ln or 'deployment' in ln or 'domain' in ln or 'customdomain' in ln:
        show_schema(n)
