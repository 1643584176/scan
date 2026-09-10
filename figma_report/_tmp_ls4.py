# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_sq1_map.txt', encoding='utf-8').read().splitlines()
targets = ('plans', 'billing', 'subscriptions', 'checkout_session', 'tax', 'orgs', 'workspace', 'weave', 'versions')
cur = None
mode = None
print('=== A. 目标域清单 ===')
for l in t:
    if l.startswith('====='):
        mode = l
        continue
    m = re.match(r'^-- ([a-z_0-9]+) \((\d+)\) --', l)
    if m:
        cur = m.group(1)
        if cur in targets and '未深测' in (mode or ''):
            print(f'-- {cur} --')
        continue
    if cur in targets and l.strip().startswith('/') and '未深测' in (mode or ''):
        print('  ' + l.strip())

print()
print('=== B. 高价值未测专区(全部) ===')
mode = None
hival = False
for l in t:
    if l.startswith('====='):
        hival = '高价值未测' in l
        continue
    if hival and l.strip():
        print(l)
