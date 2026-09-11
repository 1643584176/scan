# -*- coding: utf-8 -*-
import io, glob, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
for f in glob.glob('Figma-H1-admin_requests*'):
    t = io.open(f, encoding='utf-8', errors='replace').read()
    print('=' * 30, f, len(t))
    print('\n'.join(t.splitlines()[:40]))
print()
print('=== max_results / maxResults 出现统计 ===')
for f in glob.glob('*.py'):
    t = io.open(f, encoding='utf-8', errors='replace').read()
    n = len(re.findall(r'max_results|maxResults', t))
    if n:
        print(f, n)
