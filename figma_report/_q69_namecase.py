# -*- coding: utf-8 -*-
# q69: 「框架裂缝」核查——参数名三态（蛇形/驼峰/内部名）的历史覆盖
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = r'D:\scan\figma_report'
files = [f for f in glob.glob(os.path.join(d, '_*.py')) if '_q69' not in f]

groups = {
    'A. 驼峰名命中（notif系）': r"planId|planType|notificationType|frequencies_|recipientSettings",
    'B. 驼峰名命中（folder/thumbs系）': r"sortColumn|sortOrder|pageSize|maxResults|editorType|folderId|startTimestamp|endTimestamp",
    'C. r227 参数合并打了什么': r"^(?!#).*(planId|驼峰|camel|snake|蛇形)",
    'D. 名字大小写变体': r"(PLAN_ID|Plan_Id|plan_Id|SORT_COLUMN|Sort_Column|Name\b.*大小写|大小写)",
}
for name, p in groups.items():
    print(f'\n===== {name} =====')
    rx = re.compile(p)
    hits = 0
    seen_files = set()
    for f in files:
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for i, line in enumerate(t.splitlines(), 1):
            if rx.search(line):
                hits += 1
                fbn = os.path.basename(f)
                if fbn not in seen_files and len(seen_files) < 20:
                    seen_files.add(fbn)
                    print(f'  {fbn}:{i}: {line.strip()[:140]}')
    print(f'  → 总命中行: {hits}, 涉及文件: {len(seen_files)}+')

print('\n===== E. r227 脚本头部 =====')
try:
    lines = open('_figma_r227_param_merge.py', encoding='utf-8', errors='replace').read().splitlines()
    for i, l in enumerate(lines[:40], 1):
        print(f'  {i}: {l[:140]}')
except Exception as e:
    print('ERR', e)
print('DONE q69')
