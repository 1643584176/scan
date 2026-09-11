# -*- coding: utf-8 -*-
"""从 bf51118a 会话抽 r155-r162 的实跑记录(跨参数/尾剥离/中性化/注释族)"""
import io, os

P = r'C:/Users/tndc2/.qoder/cache/projects/scan-72ece876/conversation-history/bf51118a/bf51118a.jsonl'
txt = io.open(P, encoding='utf-8', errors='ignore').read()

KEYS = ['跨参数', '尾剥离', '中性化', '注释族', '条件消失', 'r159', 'r160', 'r161', 'r162']

def show(k, n=3, w=1500):
    idx = 0
    c = 0
    while c < n:
        i = txt.find(k, idx)
        if i < 0:
            break
        seg = txt[max(0, i - w):i + w]
        seg = seg.replace('\\n', '\n').replace('\\"', '"').replace('\\u00b5', 'µ')
        print('=' * 30, k, '@%d' % i)
        print(seg)
        print()
        idx = i + 1
        c += 1

for k in ['跨参数']:
    show(k, 3, 1800)
