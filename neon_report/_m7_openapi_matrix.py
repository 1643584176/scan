# -*- coding: utf-8 -*-
"""OpenAPI 全量端点覆盖矩阵: 按 tag 统计端点数 + 列出全部 operationId
用途: 对照历史测试面找未测类别"""
import json
from collections import defaultdict

d = json.load(open('_openapi_v2.json', encoding='utf-8'))
tags = defaultdict(list)
for p, v in d['paths'].items():
    for m, op in v.items():
        if m not in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options'):
            continue
        for t in op.get('tags', ['(untagged)']):
            tags[t].append((m.upper(), p, op.get('summary', ''), op.get('x-stability-level', ''), op.get('deprecated', False)))

print('=== tags 统计 ===')
for t in sorted(tags):
    eps = tags[t]
    print('%-32s %3d 端点  %s' % (t, len(eps), 'beta:' + str(sum(1 for e in eps if e[3] == 'beta')) + ' dep:' + str(sum(1 for e in eps if e[4]))))

print('\n=== beta/deprecated 端点全集 ===')
for t in sorted(tags):
    for m, p, s, stab, dep in tags[t]:
        if stab == 'beta' or dep:
            print('[%s] %-6s %-70s %s%s' % (t[:26], m, p[:68], s[:40], ' DEP' if dep else ''))
