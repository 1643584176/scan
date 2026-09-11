# -*- coding: utf-8 -*-
# q71: 「名字全集」机械核查——历史用过的参数名（URL+params dict）vs 候选新名字
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'
files = glob.glob(os.path.join(D, '_*.py'))

used = set()
rx_url = re.compile(r'[?&]([a-zA-Z_][a-zA-Z0-9_]*)=')
rx_key = re.compile(r"['\"]([a-z][a-z0-9_]{2,40})['\"]\s*:")
for f in files:
    try:
        t = open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    used.update(rx_url.findall(t))
    used.update(rx_key.findall(t))

print(f'===== 历史用过的名字总数: {len(used)} =====')
print(sorted(used))

# 候选清单（从未或极少出现过的"新关键字"）
cands = [
    # 时间过滤族（sort_column 白名单 touched_at/created_at 暗示）
    'touched_after', 'touched_before', 'created_after', 'created_before',
    'since', 'until', 'modified_after', 'modified_before',
    # 分页族
    'page', 'per_page', 'offset', 'limit', 'cursor', 'skip', 'take', 'count',
    # 排序族
    'sort', 'order', 'direction', 'dir', 'column', 'sort_by', 'sortBy', 'field', 'order_by',
    # Rails/Rack 框架族
    'format', '_method', 'action', 'controller', 'utf8', 'commit', 'locale', 'lang',
    # 搜索/过滤族
    'q', 'query', 'search', 'filter', 'keyword', 'term', 'name_filter', 'file_name',
    # Figma 特有
    'fetch_only_trashed_with_folder_files', 'fetch_only_shared_with_me',
    'project_id', 'team_id', 'org_id', 'resource_type', 'file_key', 'node_id',
    'trashed', 'trash', 'deleted', 'editor_type', 'file_type',
    # 垃圾对照
    'totally_unknown_xyz',
]
print('\n===== 候选名 vs 历史使用：差集（从未用过） =====')
for c in cands:
    hit = 'USED' if c in used else 'NEVER'
    print(f'  {c:42s} {hit}')
print('DONE q71')
