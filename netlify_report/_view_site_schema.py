# -*- coding: utf-8 -*-
"""查看 swagger: POST /sites 创建 schema + collaborator/member 相关 path"""
import yaml, json

spec = yaml.safe_load(open(r'D:\scan\netlify_report\_openapi\swagger.yml', encoding='utf-8'))
paths = spec['paths']

def dump_schema(sch, indent='    '):
    """递归打印 schema(截断)"""
    t = sch.get('type', '?')
    if t == 'object':
        props = sch.get('properties', {})
        print('%s(object props: %s)' % (indent, list(props.keys())[:40]))
        return
    if '$ref' in sch:
        print('%s$ref: %s' % (indent, sch['$ref'].split('/')[-1]))
        return
    print('%stype=%s enum=%s' % (indent, t, sch.get('enum', '')))

print('=== POST /sites 定义 ===')
op = paths['/sites'].get('post', {})
print('summary:', op.get('summary'))
rb = op.get('requestBody', {})
for ct, cdef in rb.get('content', {}).items():
    sch = cdef.get('schema', {})
    ref = sch.get('$ref', '')
    print('body content-type:', ct, 'schema ref:', ref)
    if ref:
        name = ref.split('/')[-1]
        dsch = spec['components']['schemas'][name]
        print('  props:', list(dsch.get('properties', {}).keys()))
    else:
        dump_schema(sch)

print()
print('=== 含 collaborator/member/invite 的 path ===')
for p in sorted(paths.keys()):
    if any(k in p.lower() for k in ['member', 'collabor', 'invite', 'user']):
        print(' ', p, '->', [m for m in paths[p] if m in ('get','post','put','patch','delete')])
