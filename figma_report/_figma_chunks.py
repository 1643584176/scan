# -*- coding: utf-8 -*-
"""从 935-*.js 提取 webpack chunk 映射,定位 figma_app 主 bundle"""
import re, os

D = 'D:/scan/figma_report/_js/'
c = open(os.path.join(D, '935-431f89677a39072c.min.js'), 'r', encoding='utf-8', errors='ignore').read()
names = set(re.findall(r'[a-zA-Z0-9_~]+-[0-9a-f]{8,}\.min\.js\.br', c))
print('chunk refs:', len(names))
for n in sorted(names):
    print(' ', n[:80])
print()
for m in re.finditer(r'figma_app[^"\']{0,100}', c):
    print('figma_app ctx:', m.group(0)[:110])
