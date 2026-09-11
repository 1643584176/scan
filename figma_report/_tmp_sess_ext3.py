# -*- coding: utf-8 -*-
"""补: 两个重要修正点 (r163 验证矩阵) 完整段"""
import io

P = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history/bf51118a/bf51118a.jsonl'
txt = io.open(P, encoding='utf-8', errors='ignore').read()

def show(k, n=2, w=6500, back=200):
    idx = 0
    c = 0
    while c < n:
        i = txt.find(k, idx)
        if i < 0:
            break
        seg = txt[max(0, i - back):i + w]
        seg = seg.replace('\\n', '\n').replace('\\"', '"').replace('\\u00b5', 'µ')
        print('#' * 40, k, '@%d' % i)
        print(seg)
        print()
        idx = i + 1
        c += 1

show('两个重要修正点', 1, 7000)
