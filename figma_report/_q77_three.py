# -*- coding: utf-8 -*-
# q77: 三线核查——A) teams/{id}/folders 历史覆盖 B) keyword 端点定位 C) 写面清单
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'
py = [f for f in glob.glob(os.path.join(D, '_*.py')) if '_q77' not in f]

print('===== A. teams/{id}/folders 历史覆盖 =====')
pats = [r'teams/[^/]*/folders', r'TeamFolders', r'getTeamFolders', r'team_folders']
for p in pats:
    cnt = 0; sample = ''
    for f in py:
        try: t = open(f, encoding='utf-8', errors='replace').read()
        except: continue
        for m in re.finditer(p, t):
            cnt += 1
            if not sample:
                i = m.start(); sample = f'{os.path.basename(f)}: ...{t[max(0,i-80):i+80]}...'.replace('\n',' ')
    print(f'  {p:28s} {cnt:4d}   {sample[:160]}')

print('\n===== B. keyword 端点定位（JS 上下文） =====')
jsfiles = glob.glob(os.path.join(D, '_js', '**', '*.js'), recursive=True)
kws = ['keyword', 'file_name', 'search_query', 'filter_by']
for kw in kws:
    dist = {}
    for f in jsfiles:
        try: t = open(f, encoding='utf-8', errors='replace').read()
        except: continue
        c = t.count(kw)
        if c: dist[os.path.basename(f)] = c
    top = sorted(dist.items(), key=lambda x:-x[1])[:4]
    print(f'\n  -- {kw}: 分布 top {top}')
# keyword 的 URL 附近上下文
print('\n  -- keyword 附近的 t.url / get(/post( 上下文 --')
shown = 0
for f in jsfiles:
    try: t = open(f, encoding='utf-8', errors='replace').read()
    except: continue
    for m in re.finditer(r'keyword', t):
        st = max(0, m.start()-260)
        seg = t[st:m.end()+120]
        if 't.url' in seg or 'get(' in seg or 'post(' in seg or '/api' in seg:
            print(f'  --- {os.path.basename(f)} ---')
            print('   ', seg.replace('\n',' ')[:400])
            shown += 1
            if shown >= 6: break
    if shown >= 6: break

print('\n===== C. 935 写面清单（put/post/del + body 键） =====')
F = os.path.join(D, '_js', '935-431f89677a39072c.min.js')
t = open(F, encoding='utf-8', errors='replace').read()
rx = re.compile(r't\.(put|post|del)\(t\.url`([^`]+)`(?:\s*,\s*([^)]{0,150}))?')
seen = set()
for m in rx.finditer(t):
    meth, ep, body = m.group(1), m.group(2), m.group(3) or ''
    key = (meth, ep)
    if key in seen: continue
    seen.add(key)
    print(f'  {meth.upper():4s} {ep[:80]:80s} body={body[:80]}')
print(f'  写面端点数: {len(seen)}')
print('DONE q77')
