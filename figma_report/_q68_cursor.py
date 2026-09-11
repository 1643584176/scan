# -*- coding: utf-8 -*-
# q68: 第 4 条候选核查——comments 分页 cursor 域 + /api/resources/ UUID 位覆盖史
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = r'D:\scan\figma_report'
files = [f for f in glob.glob(os.path.join(d, '_*.py')) if '_q68' not in f]

groups = {
    'A. comments 端点出现': r"resources/[^\"']*comments|comments\?page|cursor|next_page",
    'B. resources/ UUID 位引号形态': r"resources/[^\n]{0,60}(%27|'|;|%3B|OR\s)",
    'C. cursor 改篡改形态': r"cursor[^\n]{0,50}(%27|'|;|%3B|base64|decode|=)",
    'D. /api/resources/ 子端点清单': r"/api/resources/[^\n\"']{0,50}",
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
                if hits <= 14:
                    print(f'  {os.path.basename(f)}:{i}: {line.strip()[:145]}')
    print(f'  → 总命中: {hits}')

print('\n===== E. p110/p112 输出速览 =====')
import glob as g2
for fn in sorted(g2.glob('_p110*') + g2.glob('_p112*')):
    print(' ', fn)
print('DONE q68')
