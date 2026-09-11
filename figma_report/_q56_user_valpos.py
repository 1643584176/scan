# -*- coding: utf-8 -*-
# q56: 精确核查 user 族路径参数(fuid / :user_id)的「SQL 值位注入」历史覆盖
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = r'D:\scan\figma_report'
files = [f for f in glob.glob(os.path.join(d, '_*.py')) if '_q56' not in f]
print(f'扫描脚本数: {len(files)}')

pats = {
    'A. fuid 带引号/注释': r"fuid=.*(%27|'|--|%23)",
    'B. /api/user/ 路径带引号': r"api/user/[^\"'\s]*%27|api/user/[^\"'\s]*'",
    'C. /segments 任意用法': r"/segments",
    'D. /teams 路径用法(非 state)': r"user/\S+/teams",
    'E. api/user/<uid>/ 其他子路径': r"api/user/[^\s\"']*/(?!(teams|segments|state))[a-z_]+",
    'F. 裸 /api/user/<数字>（无子路径）': r"api/user/[0-9]{5,}[\"'\s\)]|api/user/\{UID",
}
for name, p in pats.items():
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
    print(f'  → 命中行数: {hits}')
print('\nDONE q56')
