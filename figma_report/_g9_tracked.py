# -*- coding: utf-8 -*-
# g9: 检查已跟踪文件惯例 + 全部非 figma_report 未跟踪文件
import subprocess, io, os
os.chdir(r'D:\scan')

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return (r.stdout or '') + (r.stderr or '')

out = []
t = run('git ls-files').split('\n')
fr = [l for l in t if l.startswith('figma_report/')]
out.append('tracked figma_report files: %d' % len(fr))
import re
pats = {'_r*.json': 0, '_r*out*.txt': 0, '_q*.txt': 0, '_figma_r*.py': 0, '.md': 0, '_waf': 0, '_r196*': 0}
for l in fr:
    b = l.split('/')[-1]
    if re.match(r'_r\d+.*\.json$', b): pats['_r*.json'] += 1
    if re.match(r'_r\d+.*out.*\.txt$', b): pats['_r*out*.txt'] += 1
    if b.startswith('_q') and b.endswith('.txt'): pats['_q*.txt'] += 1
    if b.startswith('_figma_r'): pats['_figma_r*.py'] += 1
    if b.endswith('.md'): pats['.md'] += 1
    if '_waf' in b: pats['_waf'] += 1
    if b.startswith('_r196'): pats['_r196*'] += 1
for k, v in pats.items():
    out.append('  %s: %d' % (k, v))

out.append('===== sample tracked _r196 =====')
for l in fr:
    if '_r196' in l:
        out.append('  ' + l)
        if len([x for x in out if x.startswith('  figma_report')]) > 25: break

out.append('===== all non-figma untracked =====')
st = run('git status --short').split('\n')
for l in st:
    if l.strip() and 'figma_report' not in l:
        out.append('  ' + l)

io.open(r'D:\scan\figma_report\_g9_tracked.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('DONE')
