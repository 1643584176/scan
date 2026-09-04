# -*- coding: utf-8 -*-
"""解析 spec 中 Data API/Auth/JWKS 相关请求 schema($ref 展开,只读)"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
schemas = spec['components']['schemas']

def resolve(name, depth=0, seen=None):
    """递归展开 schema;返回可 JSON 化的 dict(保留 description/enum/default)"""
    seen = seen or set()
    if name in seen:
        return {'$ref-loop': name}
    seen = seen | {name}
    s = schemas.get(name)
    if s is None:
        return {'$missing': name}
    out = {}
    for k, v in s.items():
        if k == 'allOf':
            merged = {}
            for sub in v:
                if '$ref' in sub:
                    merged.update(resolve(sub['$ref'].split('/')[-1], depth + 1, seen))
                else:
                    merged.update(sub)
            out['allOf-merged'] = merged
        elif k == '$ref':
            out.update(resolve(v.split('/')[-1], depth + 1, seen))
        elif k == 'properties':
            out['properties'] = {}
            for pn, pv in v.items():
                desc = pv.get('description', '')
                if len(desc) > 140:
                    desc = desc[:137] + '...'
                item = {}
                if 'type' in pv: item['type'] = pv['type']
                if 'enum' in pv: item['enum'] = pv['enum']
                if 'default' in pv: item['default'] = pv['default']
                if 'format' in pv: item['format'] = pv['format']
                if '$ref' in pv:
                    item['$ref'] = pv['$ref'].split('/')[-1]
                if desc: item['desc'] = desc
                if pv.get('items') and isinstance(pv['items'], dict):
                    if '$ref' in pv['items']:
                        item['items-ref'] = pv['items']['$ref'].split('/')[-1]
                    elif pv['items'].get('enum'):
                        item['items-enum'] = pv['items']['enum']
                if 'additionalProperties' in pv and pv['additionalProperties'] is not False:
                    item['addProps'] = True
                if 'nullable' in pv: item['nullable'] = pv['nullable']
                if 'readOnly' in pv: item['readOnly'] = pv['readOnly']
                out['properties'][pn] = item
        elif k in ('description', 'required', 'type', 'enum', 'default', 'format',
                   'x-internal', 'example', 'additionalProperties'):
            vv = v
            if isinstance(v, str) and len(v) > 200:
                vv = v[:197] + '...'
            out[k] = vv
    return out

targets = [
    'ProjectCreateRequest',
    'EnableNeonAuthIntegrationRequest',
    'DataAPICreateRequest',
    'DatabaseCreateRequest',
    'NeonAuthCreateIntegrationRequest',
    'AddProjectJWKSRequest',
    'ProjectJWKS',
]
for name in targets:
    print('\n==== schema: %s ====' % name)
    print(json.dumps(resolve(name), ensure_ascii=False, indent=1)[:3500])
