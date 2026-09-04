# -*- coding: utf-8 -*-
"""查 requestIdManager 类定义(可能在独立 chunk)"""
import re, glob, os

D = 'D:/scan/figma_report/_js/'
# 在所有已下载 js 中找 requestIdManager 定义
for p in glob.glob(D + '*.min.js'):
    d = open(p, 'r', encoding='utf-8', errors='ignore').read()
    hits = re.findall(r'requestIdManager.{0,120}', d)
    if hits:
        print(p, ':', hits[0][:120])
# 主 bundle 里 getRequestId 完整实现
d = open(D + 'figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()
i = d.find('requestIdManager')
while i >= 0 and i < len(d):
    seg = d[max(0, i - 300):i + 300]
    if 'class' in seg or 'getRequestId' in seg:
        print('CONTEXT:', seg.replace('\n', ' ')[:600])
        print()
    i = d.find('requestIdManager', i + 1)
    if i > 7000000:
        break
