# -*- coding: utf-8 -*-
"""全会话目录扫描: 找 r155-r162 的实跑输出"""
import io, os

BASE = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history'
KEYS = ['r161_crossparam', 'r159_neutralize', 'r160_striptable', 'r162_headmatrix',
        'r155_commentfam', '参数中性化', '跨参数', '尾剥离']

for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    for fn in os.listdir(dp):
        if not fn.endswith('.jsonl'):
            continue
        p = os.path.join(dp, fn)
        sz = os.path.getsize(p)
        txt = io.open(p, encoding='utf-8', errors='ignore').read()
        hits = {k: txt.count(k) for k in KEYS if txt.count(k)}
        flag = ' <<<<<' if hits else ''
        print('%-12s %9d  %s%s' % (d, sz, hits if hits else '', flag))
