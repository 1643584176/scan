# -*- coding: utf-8 -*-
"""递归展开引用链找最终字段"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
schemas = spec['components']['schemas']
seen = set()

def show_fields(n, depth=0):
    if n in seen or depth > 6:
        return
    seen.add(n)
    s = schemas.get(n)
    if not s:
        return
    req = s.get('required', [])
    print('  ' * depth + '## %s (required=%s)' % (n, req))
    for comb in ('allOf', 'oneOf', 'anyOf'):
        for ref in s.get(comb, []):
            rr = ref.get('$ref', '')
            if rr:
                show_fields(rr.split('/')[-1], depth + 1)
    for k, v in s.get('properties', {}).items():
        t = v.get('type', '')
        desc = str(v.get('description', ''))[:100]
        extra = ''
        if '$ref' in v:
            t = v['$ref'].split('/')[-1]
            show_fields(t, depth + 1)
        elif v.get('items'):
            it = v['items']
            if '$ref' in it:
                extra = ' items:%s' % it['$ref'].split('/')[-1]
                show_fields(it['$ref'].split('/')[-1], depth + 1)
            else:
                extra = ' items:%s' % json.dumps(it, ensure_ascii=False)[:150]
        ex = v.get('example')
        if ex is not None:
            extra += ' ex:%s' % json.dumps(ex, ensure_ascii=False)[:130]
        if v.get('enum'):
            extra += ' enum:%s' % v['enum']
        print('  ' * depth + '  - %-22s %-20s %s %s' % (k, t, desc, extra))

show_fields('AnnotationCreateValueRequest')
print('\n\n--- done, seen:', sorted(seen))
