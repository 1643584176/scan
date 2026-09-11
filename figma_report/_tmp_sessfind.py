# -*- coding: utf-8 -*-
"""在会话记录里找 r155-r165(尤其 r159/r160/r161/r162 跨参数/中性化/剥离)的实跑输出"""
import io, os, json, re

BASE = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history'
SESS = ['2aac2c45/2aac2c45.jsonl', '97115b46/97115b46.jsonl']
KEYS = ['r161_crossparam', 'r159_neutralize', 'r160_striptable', 'r162_headmatrix',
        'r155_commentfam', '中性化', '跨参', 'X1', 'H1']

for rel in SESS:
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print('MISSING', rel)
        continue
    print('#' * 20, rel, os.path.getsize(p))
    txt = io.open(p, encoding='utf-8', errors='ignore').read()
    for k in KEYS:
        n = txt.count(k)
        print('   %-18s x%d' % (k, n))
