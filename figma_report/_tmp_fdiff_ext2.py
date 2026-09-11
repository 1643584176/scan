# -*- coding: utf-8 -*-
"""抽 bf51118a: file_diff 全命中 + r144/真实checkpoint/VID 三线索"""
import io

P = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history/bf51118a/bf51118a.jsonl'
txt = io.open(P, encoding='utf-8', errors='ignore').read()
print('TOTAL', len(txt))

def show(k, n=10, w=2200, back=600):
    idx = 0
    c = 0
    while c < n:
        i = txt.find(k, idx)
        if i < 0:
            break
        seg = txt[max(0, i - back):i + w]
        seg = seg.replace('\\n', '\n').replace('\\"', '"').replace('\\u00b5', 'µ')
        print('=' * 30, '%r' % k, n and ('#%d' % (c + 1)), '@%d' % i)
        print(seg)
        print()
        idx = i + 1
        c += 1

show('file_diff', 8, 1600, 400)
print()
for k in ['r144', '真实 checkpoint', '2394436713245131286']:
    show(k, 1, 3000, 1200)
