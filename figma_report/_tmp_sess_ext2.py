# -*- coding: utf-8 -*-
"""抽 bf51118a 里: 后端代码还原(伪代码) + 中性化/净剥/宽容度 的完整段落"""
import io

P = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history/bf51118a/bf51118a.jsonl'
txt = io.open(P, encoding='utf-8', errors='ignore').read()
print('TOTAL', len(txt))

def show(k, n=2, w=3500, back=300):
    idx = 0
    c = 0
    while c < n:
        i = txt.find(k, idx)
        if i < 0:
            break
        seg = txt[max(0, i - back):i + w]
        seg = seg.replace('\\n', '\n').replace('\\"', '"').replace('\\u00b5', 'µ').replace('\\u003c', '<').replace('\\u003e', '>')
        print('#' * 40, k, '@%d' % i)
        print(seg)
        print()
        idx = i + 1
        c += 1

show('代码还原', 2, 6000)
print()
show('净剥', 2, 2500)
