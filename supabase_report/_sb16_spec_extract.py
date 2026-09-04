# -*- coding: utf-8 -*-
"""公开侦察16: 从 Scalar HTML 提取完整 OpenAPI spec -> JSON"""
import os, json, re

here = os.path.dirname(os.path.abspath(__file__))
body = open(os.path.join(here, '_sb15_spec_page.html'), encoding='utf-8').read()
out = []

# 找 "content": { 后 spec 对象边界 (括号深度)
i = body.find('"content": {')
out.append('content @%d' % i)
start = body.find('{', i)
depth = 0
in_str = False
esc = False
end = -1
for j in range(start, len(body)):
    ch = body[j]
    if in_str:
        if esc:
            esc = False
        elif ch == '\\':
            esc = True
        elif ch == '"':
            in_str = False
        continue
    if ch == '"':
        in_str = True
    elif ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            end = j + 1
            break
spec_txt = body[start:end]
out.append('spec json len %d' % len(spec_txt))
spec = json.loads(spec_txt)

# 保存
open(os.path.join(here, '_sb16_openapi.json'), 'w', encoding='utf-8').write(
    json.dumps(spec, indent=1, ensure_ascii=False))

# 统计
out.append('openapi %s title %s' % (spec.get('openapi'), spec.get('info', {}).get('title', '')))
out.append('version %s' % spec.get('info', {}).get('version', ''))
paths = spec.get('paths', {})
out.append('paths %d' % len(paths))
rows = []
for p, ops in paths.items():
    for method, op in ops.items():
        if method in ('get', 'post', 'put', 'patch', 'delete'):
            rows.append('%s %s -> %s' % (method.upper().ljust(6), p, op.get('operationId', '')))
out.append('operations %d' % len(rows))
out.extend(sorted(rows))
schemas = spec.get('components', {}).get('schemas', {})
out.append('schemas %d' % len(schemas))
sec = spec.get('components', {}).get('securitySchemes', {})
out.append('securitySchemes %s' % list(sec.keys()))
out.append('global security %s' % json.dumps(spec.get('security', []))[:300])

open(os.path.join(here, '_sb16_spec_summary.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:15]))
