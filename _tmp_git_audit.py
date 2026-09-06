# -*- coding: utf-8 -*-
"""Audit git state: what is staged / tracked / ignored under report dirs."""
import re
import subprocess

ROOT = 'F:/scan'

def git(*args):
    r = subprocess.run(['git', '-C', ROOT] + list(args),
                       capture_output=True, text=True, errors='replace')
    return r.stdout

print('=== .gitignore lines mentioning report/_src/_runtime/_probes ===')
lines = open(ROOT + '/.gitignore', encoding='utf-8', errors='replace').read().splitlines()
for i, l in enumerate(lines, 1):
    if re.search(r'report|_src|_runtime|_probes|_kiwi|_ref', l):
        print(i, repr(l))

print()
print('=== staged (cached) files top-level of matomo_report ===')
staged = git('diff', '--cached', '--name-only').splitlines()
print('staged total:', len(staged))
for f in staged:
    if f.startswith('matomo_report/'):
        rel = f[len('matomo_report/'):]
        print(' ', rel.split('/')[0], '<-', rel[:110])
