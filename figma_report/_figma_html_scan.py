# -*- coding: utf-8 -*-
"""app_file.html 资源引用分析:找 figma_app 主 bundle hash"""
import re

c = open('D:/scan/figma_report/_js/app_file.html', 'r', encoding='utf-8', errors='ignore').read()
for pat in [r'figma_app[^"\']{0,80}', r'webpack-artifacts[^"\']{0,100}', r'preload[^>]{0,150}']:
    print('== %s ==' % pat)
    seen = set()
    for m in re.finditer(pat, c):
        g = m.group(0)
        if g not in seen:
            seen.add(g)
            print(' ', g[:130])
    print()
