# -*- coding: utf-8 -*-
"""app_file.html 9 个内联脚本内容"""
import re

c = open('D:/scan/figma_report/_js/app_file.html', 'r', encoding='utf-8', errors='ignore').read()
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', c, re.S)
print('inline count:', len(scripts))
for i, s in enumerate(scripts):
    s = s.strip()
    print('=== script %d len %d ===' % (i, len(s)))
    print(s[:1500].replace('\n', ' ')[:1500])
    print()
    # 找 chunk 映射
    for m in re.finditer(r'\{[0-9]{1,5}:"[0-9a-f]{8,40}"[^{}]{0,3000}\}', s):
        g = m.group(0)
        if g.count('":"') > 3:
            print('  CHUNKMAP:', g[:600])
