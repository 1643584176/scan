# -*- coding: utf-8 -*-
"""q23: 盲区精确判定 —— 候选端点/参数 在历史测试脚本中的命中计数（本地零请求）
命中=0 → 从未打过（真盲区）；命中>0 → 已覆盖（列出命中脚本名供复核）
"""
import sys, io, re, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'D:\scan\figma_report'

# 收集全部历史测试脚本（含落盘 txt 也算测试痕迹）
scripts = {}
for f in os.listdir(DIR):
    if f.endswith('.py') and (f.startswith('_figma_') or f.startswith('_tmp_') or f.startswith('_q') or f.startswith('_et')):
        try: scripts[f] = open(os.path.join(DIR, f), encoding='utf-8', errors='ignore').read()
        except Exception: pass
    elif f.endswith('.txt') and f.startswith('_r'):
        try: scripts[f] = open(os.path.join(DIR, f), encoding='utf-8', errors='ignore').read()
        except Exception: pass

print(f'scripts(+落盘) loaded: {len(scripts)}')

# ============ 候选 A: 端点盲区 ============
endpoints = [
  '/api/resources',            # 本体列表（注意会误配子路径，需细判）
  '/api/resources/group_by_team',
  '/api/resources/home_shelf',
  '/api/resources/pinned',
  '/api/files/',               # 通配太宽不查，单独查下面的具体
  'thumbnail_guid',
  '/view',                     # 见下方专门口径
  'hub_files',
  'multiplayer',
  'recent_prototypes',
  '/api/files/batch',
  'bulk_favorite_resources_v2',
  'widgets/batch',
  'widgets/v2/versions',
  '/roles',
  'spell-check',
  'items/import',
  '/api/invites',
  'teams/create',
  'org_invites',
  'plugin_runs',
  'code_connect',
  'mcp/',
  'workspace/',
  'user_sidebar_sections',
  '/api/follows',
  'profile/merge',
  'planless_favorited',
  'resource_uses',
  'templates/',
  'prepare_insert',
  'template_canvas',
  '/duplicate',
  'recent_search',             # 已打过，复核参数
  'files/related_links',
]

def hit_count(frag, exclude_self=None):
    hits = []
    for name, txt in scripts.items():
        if exclude_self and name.startswith(exclude_self): continue
        if frag in txt: hits.append(name)
    return hits

print('\n===== A. 端点盲区初判（排除 q2x 侦查脚本自身） =====')
for ep in endpoints:
    hits = hit_count(ep, exclude_self='_q2')
    n = len(hits)
    tag = 'ZERO' if n == 0 else f'{n}'
    sample = ','.join(sorted(hits)[:4])
    print(f'  [{tag:>4}] {ep}  <= {sample}')

# ============ 候选 B: 已打面的未测参数 ============
print('\n===== B. 已打面的参数盲区 =====')
param_targets = {
  'resources/{type}/{cid} query': ['include_full_category','include_version_history','allow_internal'],
  '/api/resources 列表查询': ['resourceIds','resource_ids','locale','queryId','query_id','include_content','tags='],
  'group_by_team 族': ['num_resources_per_team','numResourcesPerTeam','include_category_slug','include_tags'],
  'recent_search 深尾': ['workspace_filter','workspaceFilter','previous_searches','previousSearches'],
  'files view 族': ['open_file_key','last_view_at','version_history'],
  'bulk_favorite 深尾': ['insert_at_index','insert_after_favorite_id','insert_before_favorite_id','section_id','sidebar_section_id'],
  'home_shelf 深尾': ['seen_resource_ids'],
  'users/batched 深尾': ['user_ids'],
  'files/batch': ['style_keys','subscribe_to_realtime'],
  'widgets v2': ['ids_to_versions','widget_ids','override_install_status'],
  'spell-check': ['word='],
  'collections import': ['cms_csv','csv'],
}
for face, params in param_targets.items():
    print(f'  -- {face}')
    for p in params:
        hits = hit_count(p, exclude_self='_q2')
        n = len(hits)
        tag = 'ZERO' if n == 0 else str(n)
        print(f'     [{tag:>4}] {p}  <= {",".join(sorted(hits)[:3])}')
