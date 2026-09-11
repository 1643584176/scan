# -*- coding: utf-8 -*-
# q72: 从 JS bundle 挖 paginated_files / folder 文件列表 的参数名线索
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'
dirs = [os.path.join(D, '_js'), os.path.join(D, '_kiwi_work')]
files = []
for dd in dirs:
    files += glob.glob(os.path.join(dd, '**', '*.js'), recursive=True)
print(f'JS 文件数: {len(files)}')

pats = {
    'paginated_files 出现': r'paginated_files',
    'fetch_only_ 家族': r'fetch_only_[a-z_]+',
    'sort_column 邻近': r'sort_column',
    'folderId 参数上下文': r'folderId',
    'search/搜索参数线索': r'(file_name|name_filter|search_query|filter_by|keyword)',
}
for name, p in pats.items():
    print(f'\n===== {name} =====')
    rx = re.compile(p)
    hits = {}
    for f in files:
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for m in rx.finditer(t):
            s = m.group(0)
            hits[s] = hits.get(s, 0) + 1
    for s, c in sorted(hits.items(), key=lambda x: -x[1])[:15]:
        print(f'  {c:4d}x  {s[:100]}')

# paginated_files 附近的上下文（部分代表文件）
print('\n===== paginated_files 上下文片段（前 5 处） =====')
cnt = 0
for f in files:
    try:
        t = open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for m in re.finditer(r'paginated_files', t):
        if cnt >= 5:
            break
        st = max(0, m.start() - 200)
        print(f'--- {os.path.basename(f)} ---')
        print(' ', t[st:m.end() + 300].replace('\n', ' ')[:500])
        cnt += 1
    if cnt >= 5:
        break
print('DONE q72')
