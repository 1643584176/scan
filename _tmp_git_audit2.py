# -*- coding: utf-8 -*-
"""Full untracked file audit: which should be committed vs ignored."""
import subprocess
from collections import Counter

ROOT = 'F:/scan'

def git(*args):
    r = subprocess.run(['git', '-C', ROOT] + list(args),
                       capture_output=True, text=True, errors='replace')
    return r.stdout

# untracked, not ignored
out = git('ls-files', '--others', '--exclude-standard').splitlines()
print('untracked total:', len(out))

# group by dir[0..1]
c1 = Counter('/'.join(f.split('/')[:1]) for f in out)
print('\n== top dir ==')
for k, v in c1.most_common(15):
    print('  %-30s %d' % (k, v))

c2 = Counter('/'.join(f.split('/')[:2]) for f in out)
print('\n== top dir2 ==')
for k, v in c2.most_common(20):
    print('  %-40s %d' % (k, v))

# non-matomo untracked files (potential commits)
print('\n== non matomo_report/_src,_runtime untracked ==')
for f in out:
    if not f.startswith('matomo_report/_src/') and not f.startswith('matomo_report/_runtime/'):
        print('  ', f)
