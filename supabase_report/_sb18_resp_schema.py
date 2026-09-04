# -*- coding: utf-8 -*-
"""公开侦察18: JIT/claim/login-role/query 端点响应 schema 提取"""
import os, json

here = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(os.path.join(here, '_sb16_openapi.json'), encoding='utf-8'))
paths = spec['paths']
comp = spec.get('components', {}).get('schemas', {})

def deref(s, depth=0):
    """把 schema 展开为紧凑文本 (处理 $ref/allOf/items)"""
    if not isinstance(s, dict):
        return str(s)
    if '$ref' in s:
        nm = s['$ref'].split('/')[-1]
        return 'REF:%s' % nm
    if 'allOf' in s:
        return ' | '.join(deref(x, depth + 1) for x in s['allOf'])
    props = []
    for k, v in s.items():
        if k == 'type':
            continue
        if k == 'properties':
            props.append('{%s}' % ', '.join('%s:%s' % (pk, deref(pv, depth + 1)) for pk, pv in v.items()))
        elif k == 'items':
            props.append('items=%s' % deref(v, depth + 1))
        elif k == 'enum':
            props.append('enum=%s' % json.dumps(v)[:200])
        elif k in ('example', 'examples'):
            props.append('eg=%s' % json.dumps(v, ensure_ascii=False)[:200])
        elif k in ('description', 'format', 'pattern', 'minLength', 'nullable'):
            pass
        else:
            props.append('%s=%s' % (k, json.dumps(v, ensure_ascii=False)[:120]))
    return (s.get('type', '') + ' ' + ' '.join(props)).strip()

wanted_kw = ['jit', 'claim', 'login-role', 'database/query', 'context', 'snippets', 'readonly']
out = []
for p, ops in paths.items():
    if not any(k in p for k in wanted_kw):
        continue
    for method, op in ops.items():
        if method not in ('get', 'post', 'put', 'patch', 'delete'):
            continue
        out.append('=' * 90)
        out.append('%s %s [%s]' % (method.upper(), p, op.get('operationId')))
        for code, resp in op.get('responses', {}).items():
            if code not in ('200', '201', '204'):
                continue
            desc = (resp.get('description') or '')[:120]
            out.append('  %s: %s' % (code, desc))
            for ct, media in resp.get('content', {}).items():
                out.append('    %s -> %s' % (ct, deref(media.get('schema', {}))[:1500]))

open(os.path.join(here, '_sb18_resp_schema.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out))
