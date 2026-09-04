# -*- coding: utf-8 -*-
"""查 BranchAnonymizedCreateRequest / MaskingRule schema 全字段"""
import json

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
schemas = spec['components']['schemas']

names = ['BranchAnonymizedCreateRequest', 'MaskingRulesUpdateRequest', 'MaskingRulesResponse',
         'AnonymizedBranchStatusResponse', 'MaskingRule', 'BranchCreateRequest']

for n in names:
    s = schemas.get(n)
    if not s:
        print('== %s: MISSING' % n)
        continue
    print('\n== %s' % n)
    print(' desc:', str(s.get('description'))[:300])
    props = s.get('properties', {})
    print(' required:', s.get('required', []))
    for k, v in props.items():
        t = v.get('type', v.get('$ref', v.get('anyOf', v.get('oneOf', ''))))
        print('  %-26s %-48s %s' % (k, json.dumps(t, ensure_ascii=False)[:70], str(v.get('description', ''))[:150]))
        if v.get('items'):
            print('    items:', json.dumps(v.get('items'), ensure_ascii=False)[:200])
        if v.get('example') is not None:
            print('    example:', json.dumps(v.get('example'), ensure_ascii=False)[:200])
