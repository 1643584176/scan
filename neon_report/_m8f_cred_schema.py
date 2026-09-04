# -*- coding: utf-8 -*-
"""Credentials 端点全 schema"""
import json

d = json.load(open('_openapi_v2.json', encoding='utf-8'))
for p, v in d['paths'].items():
    if '/credentials' in p:
        for m, op in v.items():
            if m not in ('get', 'post', 'put', 'patch', 'delete'):
                continue
            print('=== %s %s (%s)' % (m.upper(), p, op.get('summary', '')))
            rb = op.get('requestBody', {})
            if rb:
                sch = rb.get('content', {}).get('application/json', {}).get('schema', {})
                print('  body: %s' % json.dumps(sch, ensure_ascii=False)[:800])
            resp = op.get('responses', {}).get('200') or op.get('responses', {}).get('201', {})
            print('  200: %s' % json.dumps(resp.get('content', {}).get('application/json', {}).get('schema', {}), ensure_ascii=False)[:800])
# 相关 schema
for name in d['components']['schemas']:
    if 'Credential' in name or 'credential' in name:
        print('\nSCHEMA %s:' % name)
        print(json.dumps(d['components']['schemas'][name], ensure_ascii=False)[:800])
