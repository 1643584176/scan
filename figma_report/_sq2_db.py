# -*- coding: utf-8 -*-
"""_sq2_db.py 从 533 端点中只筛"DB 语义"端点:查询/过滤/导出/统计/批量/映射
分类: DBQ=纯查询类(打注入首选) / DBW=写含DB风险(批量/导入/校验) / X=纯动作(排除)
"""
import json, re, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = json.load(open('_q1_paths.json', encoding='utf-8'))

DEEP = ['folder_search', '/collections/', '/recent_search', '/resources', '/widgets/',
        '/livegraph', '/files/', 'user/state', 'session/state', 'hub_profiles',
        'code_suggestions', 'authed_users', '/me', 'related_content']

# 纯动作类(排除):这些接口参数不构成查询条件
X = re.compile(r'login|logout|approve|deny|/request|vote|save|/like|block|dismiss|'
               r'redeem|acknowledge|/grant|revoke|rotate|mark_viewed|optin|upgrade|'
               r'duplicate|/color|publish|disconnect|restore|claim|clear|resend|'
               r'reject|resolve|withdraw|complete|fulfill|/create|presence|/token|'
               r'/auth|bootstrap|override|clear_account|claim|delete|restore|preview', re.I)
# 明确查询类:参数=查询条件/过滤/排序/统计维
DBQ = re.compile(r'search|export|report|stats|analytics|count|summary|usage|logs?($|/)'
                 r'|detail|versions|file_key|content_summary|suggest|query|filter|'
                 r'group_by|folders?($|/|/files)|/files($|/)|last_edit|recent|'
                 r'activity|num_backfilled|deletion|perf|monitor|template|directory'
                 r'|source_files|published|documentation|bundles|/users$|/teams$|'
                 r'teams/|org_users|/members|license|segments|batched|deliver'
                 r'|projections|manifest|collage|inserts|palette|banner', re.I)
# 批量/导入/校验类(写但含 DB 风险)
DBW = re.compile(r'batch|bulk|import|csv|validate|move|trash|edit_lock|update_items|'
                 r'update_tax|mappings', re.I)

dbq, dbw, x = [], [], []
for path in data:
    if any(d in path for d in DEEP):
        continue
    if X.search(path) and not DBQ.search(path):
        x.append(path)
    elif DBQ.search(path):
        dbq.append(path)
    elif DBW.search(path):
        dbw.append(path)
    else:
        x.append(path)

def show(name, arr):
    print(f'\n===== {name} ({len(arr)}) =====')
    g = collections.defaultdict(list)
    for p in sorted(arr):
        segs = p.strip('/').split('/')
        g[segs[1] if len(segs) > 1 else p].append(p)
    for seg in sorted(g):
        print(f'-- {seg} ({len(g[seg])}) --')
        for p in g[seg]:
            print(f'   {p}')

print(f'总: {len(data)}  已深测: {sum(1 for p in data if any(d in p for d in DEEP))}')
print(f'DBQ(查询类): {len(dbq)}   DBW(批量写): {len(dbw)}   X(排除): {len(x)}')
show('DBQ 纯查询类(注入首选)', dbq)
show('DBW 批量/导入/校验类', dbw)
