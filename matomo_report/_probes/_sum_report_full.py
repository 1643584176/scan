# -*- coding: utf-8 -*-
import json
from collections import Counter

rows = json.load(open('_mt06_report_full.json', encoding='utf-8'))
print('total rows:', len(rows))
flags = [r for r in rows if r.get('FLAG')]
print('FLAGGED:', len(flags))
for f in flags:
    print('FLAG %s.%s idS=%s | admin=%s u2=%s u3=%s | %s'
          % (f['plugin'], f['method'], f['idsite'], f['admin'], f['user2'],
             f['user3'], f['FLAG']))

print()
print('=== distribution ===')
for who in ('admin', 'user2', 'user3'):
    c = Counter(r[who] for r in rows)
    print(who, dict(c))
