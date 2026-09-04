# -*- coding: utf-8 -*-
"""公开侦察17: 高价值 v1 端点详情提取 (JIT/claim/login-role/query/snippets/context)"""
import os, json

here = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(here, '_sb16_openapi.json'), encoding='utf-8'))
paths = spec['paths']

wanted_kw = ['jit', 'claim', 'login-role', 'query', 'snippets', 'context', 'webhooks', 'actions', 'readonly']
out = []
for p, ops in paths.items():
    if not any(k in p for k in wanted_kw):
        continue
    for method, op in ops.items():
        if method not in ('get', 'post', 'put', 'patch', 'delete'):
            continue
        out.append('=' * 100)
        out.append('%s %s  [%s]' % (method.upper(), p, op.get('operationId')))
        summ = op.get('summary', '')
        if summ:
            out.append('  summary: %s' % summ)
        desc = (op.get('description') or '').strip()
        if desc:
            out.append('  desc: %s' % desc[:500].replace('\n', ' '))
        # 参数
        for prm in op.get('parameters', []):
            sch = prm.get('schema', {})
            out.append('  param %s %s type=%s enum=%s desc=%s' % (
                prm.get('in'), prm.get('name'), sch.get('type'),
                json.dumps(sch.get('enum', []))[:120], (prm.get('description') or '')[:150].replace('\n', ' ')))
        # 请求体
        rb = op.get('requestBody', {})
        for ct, media in rb.get('content', {}).items():
            ref = media.get('schema', {}).get('$ref', '')
            out.append('  body %s ref=%s' % (ct, ref))
        # 响应状态码
        codes = list(op.get('responses', {}).keys())
        out.append('  responses: %s' % ','.join(codes))

# 各 requestBody schema 定义展开 (named)
comp = spec.get('components', {}).get('schemas', {})
name_whitelist = ['jit', 'Jit', 'JIT', 'claim', 'Claim', 'snippet', 'Snippet', 'LoginRole', 'login', 'query', 'Query']
seen = set()
for p, ops in paths.items():
    if not any(k in p for k in wanted_kw):
        continue
    for method, op in ops.items():
        rb = op.get('requestBody', {})
        for ct, media in rb.get('content', {}).items():
            ref = media.get('schema', {}).get('$ref', '')
            if ref:
                nm = ref.split('/')[-1]
                if nm in comp and nm not in seen:
                    seen.add(nm)
                    out.append('-' * 80)
                    out.append('SCHEMA %s' % nm)
                    out.append(json.dumps(comp[nm], indent=1, ensure_ascii=False)[:2200])

open(os.path.join(here, '_sb17_v1_highvalue.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out))
