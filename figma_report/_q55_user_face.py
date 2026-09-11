# -*- coding: utf-8 -*-
# q55: 本地核查 /api/user/ 形态 与 fuid / state 参数是否打过
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = r'D:\scan\figma_report'
files = [f for f in glob.glob(os.path.join(d, '_*.py')) if '_q55' not in f]
print(f'扫描脚本数: {len(files)}')

pats = {
    'A. /api/user/ 任意形态': r"api/user/",
    'B. fuid 参数': r"fuid",
    'C. /api/user/state': r"user/state",
    'D. /api/user/ 数字路径': r"api/user/\{?[a-zA-Z_]*\d|api/user/[0-9]",
    'E. /api/user/notification': r"api/user/notification",
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
                if hits <= 10:
                    print(f'  {os.path.basename(f)}:{i}: {line.strip()[:140]}')
    print(f'  → 命中行数: {hits}')
print('\nDONE q55')
