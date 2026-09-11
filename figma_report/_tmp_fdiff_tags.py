# -*- coding: utf-8 -*-
"""抽 bf51118a 里 r137/r139/r144B 的 file_diff 实跑输出标签"""
import io

P = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history/bf51118a/bf51118a.jsonl'
txt = io.open(P, encoding='utf-8', errors='ignore').read()

KEYS = ['A1_all1', 'C1_real', 'C3_cpkey', 'Hsu2ESbHyQ9YyHptrHqxav', '2394436713245131286',
        'X-Figma-Owner-Id', 'X-Figma-File-Seq', '真实 checkpoint', 'checkpoint_id', 'r144']

for k in KEYS:
    print('%-26s x%d' % (k, txt.count(k)))
