# -*- coding: utf-8 -*-
"""Logs query 端点 request schema + ai_gateway/storage/snapshot 路径定义"""
import json

d = json.load(open('_openapi_v2.json', encoding='utf-8'))

# 1. logs 路径的完整操作定义
for p, v in d['paths'].items():
    if '/logs/' in p or 'ai_gateway' in p or '/storage' in p or 'snapshots' in p:
        for m, op in v.items():
            if m not in ('get', 'post', 'put', 'patch', 'delete'):
                continue
            print('=== %s %s (%s)' % (m.upper(), p, op.get('summary', '')))
            rb = op.get('requestBody', {})
            if rb:
                sch = rb.get('content', {}).get('application/json', {}).get('schema', {})
                print('  body: %s' % json.dumps(sch, ensure_ascii=False)[:700])
            params = op.get('parameters', [])
            for pa in params:
                print('  param: %s %s' % (pa.get('name'), pa.get('schema', {}).get('type', '?')))
            resp = op.get('responses', {}).get('200', {})
            print('  200: %s' % json.dumps(resp.get('content', {}).get('application/json', {}).get('schema', {}), ensure_ascii=False)[:300])
