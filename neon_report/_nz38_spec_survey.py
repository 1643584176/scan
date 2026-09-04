# -*- coding: utf-8 -*-
"""数据管理面 spec 盘点: 提取全部端点, 标注已测面, 输出未测候选"""
import json, re

spec = json.load(open(r'D:\scan\neon_report\_openapi_v2.json', encoding='utf-8'))
paths = spec['paths']

# 已测面覆盖的路径模式(来自各归档报告)
COVERED = [
    # Auth/DataAPI 技术面 (Neon-Auth与DataAPI技术面-20260904.md)
    'auth', 'data_api', 'functions', 'ai_gateway', 'storage', 'credentials',
    'logs', 'snapshots', 'anonymized', 'masking_rules', 'webhooks', 'branches/{branch_id}/anonymize',
    # 用户面 (Neon-Auth用户面双用户测试.md)
    'neon_auth', 'sessions', 'oauth',
    # 平台库横切 (postgres 库)
    'roles', 'databases', 'memberships', 'invites', 'members',
    # 其他已闭合
    'check_availability', 'projects/{project_id}/operations',
]

def classify(path):
    """按 spec tags 无法直接拿, 用 operationId 粗分"""
    return path

rows = []
for p, methods in paths.items():
    for m, op in methods.items():
        if m not in ('get', 'post', 'put', 'patch', 'delete'):
            continue
        oid = op.get('operationId', '')
        tags = op.get('tags', [])
        covered = any(c in p or c in oid for c in COVERED)
        rows.append((m.upper(), p, oid, ','.join(tags), covered))

# 按 tag 聚合输出
from collections import Counter, defaultdict
tagcnt = Counter()
for m, p, oid, tags, cov in rows:
    for t in tags.split(','):
        if t:
            tagcnt[t] += 1
print('=== TAGS 统计 ===')
for t, n in tagcnt.most_common():
    print('  %-40s %d' % (t, n))

print('\n=== 未覆盖端点 (cov=False) 按 tag ===')
bytag = defaultdict(list)
for m, p, oid, tags, cov in rows:
    if not cov:
        bytag[tags].append((m, p, oid))
for tags, items in sorted(bytag.items()):
    print('\n## [%s] 共 %d 个' % (tags, len(items)))
    for m, p, oid in sorted(items, key=lambda x: x[1]):
        print('  %-7s %-95s %s' % (m, p, oid))
