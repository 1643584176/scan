# -*- coding: utf-8 -*-
"""展开 BranchAnonymizedCreateRequest (allOf/oneOf) 全字段"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
schemas = spec['components']['schemas']

def expand(n, depth=0):
    if depth > 4:
        return
    s = schemas.get(n)
    if not s:
        return
    print('  ' * depth + '== %s required=%s' % (n, s.get('required', [])))
    for comb in ('allOf', 'oneOf', 'anyOf'):
        if comb in s:
            print('  ' * depth + '  [%s]' % comb)
            for ref in s[comb]:
                rr = ref.get('$ref', '')
                print('  ' * depth + '   ->', rr)
                if rr:
                    expand(rr.split('/')[-1], depth + 1)
    props = s.get('properties', {})
    for k, v in props.items():
        t = v.get('type', v.get('$ref', ''))
        extra = ''
        if v.get('items'):
            it = v['items']
            extra = ' items:' + (it.get('$ref', json.dumps(it, ensure_ascii=False))[:120])
        ex = v.get('example')
        if ex is not None:
            extra += ' example:%s' % json.dumps(ex, ensure_ascii=False)[:150]
        print('  ' * depth + '  %-24s %-30s %s%s' % (k, t, str(v.get('description', ''))[:110], extra))
        # 枚举值
        if v.get('enum'):
            print('  ' * depth + '    enum:', v['enum'])

expand('BranchAnonymizedCreateRequest')
