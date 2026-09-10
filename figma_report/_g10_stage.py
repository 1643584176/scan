# -*- coding: utf-8 -*-
# g10: git add -A + staged 安全扫描(敏感关键词)
import subprocess, io, os, re
os.chdir(r'D:\scan')

def run(cmd, timeout=300):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    return (r.stdout or '') + (r.stderr or '')

out = []
# 1 verify ignore
for f in ['figma_report/_waf_cookies_new.txt', 'figma_report/_r14_recent_authed.json', 'figma_report/_r14_recent_wafonly.json']:
    r = run('git check-ignore "%s"' % f).strip()
    out.append('ignore-check %s -> %s' % (f, 'IGNORED' if r else '!!! NOT-IGNORED !!!'))

# 2 add
r = run('git add -A')
out.append('git add -A done: %s' % r.strip()[:200])

# 3 staged list
staged = run('git diff --cached --name-only').split('\n')
staged = [l for l in staged if l.strip()]
out.append('staged files: %d' % len(staged))

# 4 sensitive scan on staged
kw = ['cookie', 'token', 'sess', 'cred', 'secret', 'password', 'apikey', 'api_key', 'auth', '_waf', 'har']
hits = []
for l in staged:
    low = l.lower()
    if any(k in low for k in kw):
        hits.append(l)
out.append('sensitive-keyword hits in staged: %d' % len(hits))
for h in hits:
    out.append('  !! ' + h)

# 5 staged breakdown by dir
from collections import Counter
c = Counter()
for l in staged:
    top = l.split('/')[0] if '/' in l else '(root)'
    c[top] += 1
out.append('staged by dir:')
for d, n in c.most_common(30):
    out.append('  %5d  %s' % (n, d))

io.open(r'D:\scan\figma_report\_g10_staged.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('DONE staged:', len(staged))
