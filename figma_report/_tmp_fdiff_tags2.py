# -*- coding: utf-8 -*-
"""全会话扫描 r137/r139/r144B 输出标签,定位运行会话"""
import io, os

BASE = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history'
KEYS = ['A1_all1', 'C1_real', 'C3_cpkey', 'B8_nodes_or', 'X-Figma-Owner-Id',
        'X-Figma-File-Seq', 'fromFileVersionId', 'file_diff']

for d in sorted(os.listdir(BASE)):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp):
        continue
    for fn in os.listdir(dp):
        if not fn.endswith('.jsonl'):
            continue
        txt = io.open(os.path.join(dp, fn), encoding='utf-8', errors='ignore').read()
        hits = {k: txt.count(k) for k in KEYS if txt.count(k)}
        if hits:
            print('%-10s %s' % (d, hits))
