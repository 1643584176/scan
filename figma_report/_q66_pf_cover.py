# -*- coding: utf-8 -*-
# q66: paginated_files 家族覆盖核查——各槽位的历史打击史
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = r'D:\scan\figma_report'
files = [f for f in glob.glob(os.path.join(d, '_*.py')) if '_q66' not in f]

groups = {
    'A. paginated_files 出现处': r"paginated_files",
    'B. sort_order 注入形态': r"sort_order[^\n]{0,40}(%27|'|;|%3B|--|SELECT|OR)",
    'C. page_size 注入形态': r"page_size[^\n]{0,40}(%27|'|;|%3B|--|SELECT|OR\s)",
    'D. folderId 注入形态(query)': r"folderId[^\n]{0,40}(%27|;|%3B|SELECT|OR\s)",
    'E. folders/ 路径引号形态': r"folders/[^\n]{0,50}(%27|'|;|%3B)",
    'F. sort_column SQL语法(逗号/CASE/括号)': r"sort_column[^\n]{0,60}(,|CASE|\(|\bdesc\b)",
    'G. /api/folders/ 其它子端点': r"/api/folders/[^\n\"']{0,60}",
}
for name, p in groups.items():
    print(f'\n===== {name} =====')
    rx = re.compile(p)
    hits = 0
    for f in files:
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for i, line in enumerate(t.splitlines(), 1):
            if rx.search(line):
                hits += 1
                if hits <= 12:
                    print(f'  {os.path.basename(f)}:{i}: {line.strip()[:150]}')
    print(f'  → 总命中: {hits}')
print('DONE q66')
