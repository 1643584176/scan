# -*- coding: utf-8 -*-
"""_q1_paths.json(JS 全端点地图)分类器:按资源域分组 + 标注已深测/未测"""
import json, collections, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = json.load(open('_q1_paths.json', encoding='utf-8'))

# 已深测(本项目 r80-r110 等):关键词匹配
DEEP = ['folder_search', '/collections/', '/recent_search', '/resources', '/widgets/',
        '/livegraph', '/files/', 'user/state', 'session/state', 'hub_profiles',
        'code_suggestions', 'authed_users', '/me', 'related_content']
PART = ['community', 'search']

groups = collections.defaultdict(list)
for path, srcs in data.items():
    segs = path.strip('/').split('/')
    seg = segs[1] if len(segs) > 1 else path
    groups[seg].append((path, srcs))

print(f'=== 全端点总数: {len(data)} | 资源域: {len(groups)} ===')

und, partd, deepd = [], [], []
for seg in sorted(groups):
    for path, srcs in sorted(groups[seg]):
        if any(d in path for d in DEEP): deepd.append(path)
        elif any(p in path for p in PART): partd.append(path)
        else: und.append(path)

print(f'[DEEP] {len(deepd)}   [PART] {len(partd)}   [NEW ] {len(und)}')

print('\n===== 未深测端点(按域) =====')
und_g = collections.defaultdict(list)
for p in und:
    segs = p.strip('/').split('/')
    und_g[segs[1] if len(segs) > 1 else p].append(p)
for seg in sorted(und_g):
    print(f'\n-- {seg} ({len(und_g[seg])}) --')
    for p in sorted(und_g[seg]):
        print(f'   {p}')

print('\n===== 部分测过(按域) =====')
pg = collections.defaultdict(list)
for p in partd:
    segs = p.strip('/').split('/')
    pg[segs[1] if len(segs) > 1 else p].append(p)
for seg in sorted(pg):
    print(f'\n-- {seg} ({len(pg[seg])}) --')
    for p in sorted(pg[seg]):
        print(f'   {p}')

# 高价值筛选:含路径变量/export/搜索/报表/批量
print('\n===== 高价值未测(路径变量/导出/搜索/批量/报表) =====')
import re
HV = re.compile(r'\$\{|export|search|report|import|bulk|batch|list|query|count|stats|activity|log', re.I)
for p in sorted(und):
    if HV.search(p):
        print(f'   {p}')
