# -*- coding: utf-8 -*-
# g8: git 状态全量盘点(敏感文件/figma_report/统计)
import subprocess, io, os
os.chdir(r'D:\scan')

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return (r.stdout or '') + (r.stderr or '')

out = []
out.append('===== tracked sensitive =====')
t = run('git ls-files')
sens = [l for l in t.split('\n') if any(k in l.lower() for k in ['cookie', 'token', 'sess', 'cred'])]
out.append('count: %d' % len(sens))
for s in sens[:30]:
    out.append('  ' + s)

out.append('===== status summary =====')
st = run('git status --short')
lines = [l for l in st.split('\n') if l.strip()]
out.append('total status lines: %d' % len(lines))
from collections import Counter
dirs = Counter()
for l in lines:
    p = l[3:].strip().strip('"')
    top = p.split('/')[0] if '/' in p else '(root)'
    dirs[top] += 1
for d, c in dirs.most_common(25):
    out.append('  %5d  %s' % (c, d))

out.append('===== figma_report status =====')
fr = [l for l in lines if 'figma_report' in l]
out.append('figma_report lines: %d' % len(fr))
for l in fr[:80]:
    out.append('  ' + l)

out.append('===== check-ignore keys =====')
for f in ['figma_report/_waf_cookies_new.txt', 'figma_report/Figma-SQL注入总账-2026-09-10.md',
          'figma_report/_r196aq_r1.txt', 'figma_report/_q6_l6.txt', 'figma_report/_g1_scripts.py',
          'figma_report/_g2_src.py', 'figma_report/_q1_paths.json', 'figma_report/_r196ap_a3.txt']:
    r = run('git check-ignore "%s"' % f).strip()
    out.append('  %s -> %s' % (f, 'IGNORED' if r else 'NOT-ignored'))

out.append('===== untracked sensitive scan (all ?? files) =====')
for l in lines:
    if l.startswith('??'):
        p = l[3:].strip().strip('"')
        low = p.lower()
        if any(k in low for k in ['cookie', 'token', 'sess', '_waf', 'auth', 'secret', 'cred']):
            out.append('  !! ' + p)

io.open(r'D:\scan\figma_report\_g8_gitstat.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('DONE', len(out), 'lines')
