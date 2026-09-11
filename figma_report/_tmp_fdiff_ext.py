# -*- coding: utf-8 -*-
"""从 bf51118a 抽 checkpoint_diff 全部实跑输出(r137/r139/r144B 结果)"""
import io

P = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history/bf51118a/bf51118a.jsonl'
txt = io.open(P, encoding='utf-8', errors='ignore').read()

idx = 0
n = 0
while True:
    i = txt.find('checkpoint_diff', idx)
    if i < 0:
        break
    n += 1
    seg = txt[max(0, i - 2500):i + 4500]
    seg = seg.replace('\\n', '\n').replace('\\"', '"').replace('\\u00b5', 'µ')
    print('=' * 35, 'HIT', n, '@%d' % i)
    print(seg)
    print()
    idx = i + 1
