# -*- coding: utf-8 -*-
"""找 viewHasStaticQueries 定义 + requestIdManager 完整实现(所有 chunk)"""
import re, glob, os

D = 'D:/scan/figma_report/_js/'
d = open(D + 'figma_app-main.js', 'r', encoding='utf-8', errors='ignore').read()
for pat in [r'viewHasStaticQueries[^;]{0,200}', r'staticQuer[^;]{0,150}', r'hasStaticQueries[^;]{0,150}']:
    for m in list(re.finditer(pat, d))[:6]:
        print(pat, '=>', m.group(0)[:220])
    print()
