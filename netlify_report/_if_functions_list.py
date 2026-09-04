# -*- coding: utf-8 -*-
"""1. manage-extension-proxy 的所有调用上下文
2. net_app.js 中全部 /.netlify/functions/* 路径清单"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

paths = sorted(set(re.findall(r'/(?:\.netlify/functions/[A-Za-z0-9_.\-]+|\.netlify/functions/extension-proxy)', data)))
print('== functions 路径清单 ==')
for p in paths:
    print(' ', p)
print()

# manage-extension-proxy 调用点(包括 mutation:slug/body/method)
idx = [m.start() for m in re.finditer(r'manage-extension-proxy', data)]
print('== manage-extension-proxy 上下文 ==')
for i in idx:
    seg = data[i - 600:i + 900]
    # 找 method/body/action 关键词
    print('---ctx---')
    print(seg.replace('\n', ' ')[:1400])
    print()
