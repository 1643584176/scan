# -*- coding: utf-8 -*-
"""提取 OpenAPI Functions tag 路径定义"""
import json

d = json.load(open('D:/scan/neon_report/_openapi_v2.json', encoding='utf-8'))
paths = d.get('paths', {})
tags = d.get('tags', [])
print('=== tags ===')
for t in tags:
    print(' ', t.get('name'), '-', t.get('description', '')[:80])

# 按 path 收集 operation 的 tag
from collections import defaultdict
tagpaths = defaultdict(list)
for p, ops in paths.items():
    for m, op in ops.items():
        if not isinstance(op, dict):
            continue
        for tg in op.get('tags', []):
            tagpaths[tg].append((m.upper(), p))

print('\n=== Functions tag paths ===')
for m, p in tagpaths.get('Functions', []):
    print(' %s %s' % (m, p))

print('\n=== all tags path counts ===')
for tg in tagpaths:
    print(' %s: %d' % (tg, len(tagpaths[tg])))
