# -*- coding: utf-8 -*-
# q64: 「再想 SQL」核查——A.user族兄弟词 B.排序/分页/游标参数 C.头部家族残余 D.二级路径
import sys, io, glob, os, re
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = r'D:\scan\figma_report'
files = [f for f in glob.glob(os.path.join(d, '_*.py')) if '_q64' not in f]

# A. /api/user/<word> 词频
words = Counter()
# B. 排序/分页参数
sortpat = re.compile(r"(sort|order_by|order|direction|cursor|offset|page|per_page|limit|before|after)\s*[=:]\s*[^,)}\s]")
sorthits = []
# C. 头部家族
hdrpat = re.compile(r"(If-None-Match|If-Modified-Since|X-Requested-With|Accept-Language|Accept-Encoding|X-Figma-\w+|charset=)")
hdrhits = []
# D. /api/user/:uid/teams/<second> 二级路径
secpat = re.compile(r"/teams/[a-zA-Z0-9_%{}$'\"-]+")

for f in files:
    try:
        t = open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for m in re.finditer(r"/api/user/([a-z_]+)", t):
        words[m.group(1)] += 1
    base = os.path.basename(f)
    for i, line in enumerate(t.splitlines(), 1):
        if 'req(' in line or 'get(' in line or 'go(' in line or 'requests.' in line or 'url =' in line:
            if sortpat.search(line):
                sorthits.append(f'{base}:{i}: {line.strip()[:140]}')
        if hdrpat.search(line) and ('headers' in line.lower() or "': '" in line or '": "' in line):
            hdrhits.append(f'{base}:{i}: {line.strip()[:140]}')
for m in re.finditer(r"/api/user/[^/\"']+/teams/([a-z_]+)", t):
    pass

print('===== A. /api/user/<word> 词频 =====')
for w, c in words.most_common(40):
    print(f'  {w}: {c}')

print('\n===== B. 排序/分页/游标参数命中（前25） =====')
for h in sorthits[:25]:
    print(' ', h)
print(f'  → 总命中: {len(sorthits)}')

print('\n===== C. 头部家族命中（前20） =====')
for h in hdrhits[:20]:
    print(' ', h)
print(f'  → 总命中: {len(hdrhits)}')

print('\n===== D. /teams/<第二段> 形态 =====')
sec = Counter()
for f in files:
    try:
        t = open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for m in re.finditer(r"/api/user/[^/\"' {]+/teams/([a-zA-Z0-9_%${}'\".-]{1,40})", t):
        sec[m.group(1)[:30]] += 1
for w, c in sec.most_common(20):
    print(f'  {w}: {c}')
print('DONE q64')
