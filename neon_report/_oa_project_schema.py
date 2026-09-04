# -*- coding: utf-8 -*-
"""dump ProjectCreateRequest 完整结构"""
import json
spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
comps = spec['components']['schemas']

def show(name, depth=0, seen=None):
    seen = seen or set()
    if depth > 4 or name in seen: return
    seen.add(name)
    s = comps.get(name, {})
    print('%s== %s' % ('  ' * depth, name))
    if 'properties' in s:
        for pn, pv in s['properties'].items():
            req = 'REQ' if pn in s.get('required', []) else 'opt'
            if '$ref' in pv:
                print('%s- %s (%s) ->' % ('  ' * (depth + 1), pn, req))
                show(pv['$ref'].split('/')[-1], depth + 2, seen)
            else:
                print('%s- %s (%s) %s %s %s' % ('  ' * (depth + 1), pn, req, pv.get('type'), pv.get('enum') or '', (pv.get('description') or '')[:60]))
    else:
        print('%s  raw: %s' % ('  ' * (depth + 1), json.dumps(s)[:200]))

show('ProjectCreateRequest')
