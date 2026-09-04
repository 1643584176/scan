# -*- coding: utf-8 -*-
"""离线查 AddProjectJWKSRequest / NeonAuthCreateIntegrationRequest / auth_provider enum 细节"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
comp = spec['components']['schemas']

def dump(name, depth=0):
    sch = comp.get(name)
    if not sch or not isinstance(sch, dict):
        print(' ' * depth, name, '=', sch)
        return
    print(' ' * depth, name)
    for k, v in sch.get('properties', {}).items():
        extra = ''
        if isinstance(v, dict):
            if 'enum' in v:
                extra = ' enum=%s' % v['enum']
            if '$ref' in v:
                extra = ' -> %s' % v['$ref'].split('/')[-1]
            if v.get('type') == 'array':
                extra = ' array of %s' % v.get('items', {}).get('$ref', v.get('items', {}).get('type'))
            if 'nullable' in v:
                extra += ' nullable'
        print(' ' * (depth + 2), '%s: %s%s' % (k, v.get('type', ''), extra))
    for req in sch.get('required', []):
        print(' ' * (depth + 2), '*required:', req)

for n in ['AddProjectJWKSRequest', 'NeonAuthCreateIntegrationRequest', 'DataAPICreateRequest', 'JWKSResponse', 'JWKSItem']:
    print('=' * 60)
    dump(n)

# auth_provider 相关 enum 全局搜
print('\n==== auth_provider 字段出现处 ====')
for name, sch in comp.items():
    if isinstance(sch, dict) and 'properties' in sch:
        for k, v in sch['properties'].items():
            if k == 'auth_provider':
                print('schema:', name, '->', v)
