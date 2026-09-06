# -*- coding: utf-8 -*-
"""2688 chunk 共享 UI 上下文 + main 中 gate 消费点"""
import os, re

JS = r'F:/scan/figma_report/_js'

def show(fn, anchor, before, after, limit=3):
    c = open(os.path.join(JS, fn), encoding='utf-8', errors='ignore').read()
    print('#' * 20, fn)
    idx = 0
    n = 0
    while n < limit:
        i = c.find(anchor, idx)
        if i < 0:
            break
        print(f'--- @{i} ---')
        print(c[max(0, i - before):i + after].replace('\n', ' '))
        print()
        idx = i + 1
        n += 1

show('2688-74090ce86ecdf35c.min.js', 'activeAiChatThread)?.privacyMode', 1400, 900)
show('figma_app-main.js', 'ai_assistant_sharing"', 600, 400)
