# -*- coding: utf-8 -*-
import re

lines = open('_mt06_sqldiff_out.txt', encoding='utf-8', errors='replace').read().splitlines()
# find statements mentioning archive / log_visit / log_conversion
keys = []
for i, l in enumerate(lines):
    s = l.strip()
    if not s or s.startswith('26') or s.startswith('---') or s.startswith('=') or s.startswith('SQL'):
        continue
    if re.search(r'archive|log_visit|log_conversion|matomo_access', s, re.I):
        keys.append(s[:220])
print('matching lines:', len(keys))
for k in keys:
    print(k)
