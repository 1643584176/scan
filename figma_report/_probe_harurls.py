# -*- coding: utf-8 -*-
"""从 HAR 分析产物提取 download/export/save/copy/version 类 URL"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

txt = open(r'D:\scan\figma_report\_figma_har_analysis.txt', encoding='utf-8', errors='replace').read()
print('len', len(txt))

# URL 提取 (宽松)
urls = set()
for m in re.finditer(r'https?://[^\s"\'<>\\]+', txt):
    u = m.group(0).rstrip('),.;')
    urls.add(u)
print('total urls', len(urls))

kws = ['fig', 'download', 'export', 'save', 'copy', 'version', 'canvas', 'file', 'rev']
for u in sorted(urls):
    if any(k in u.lower() for k in kws) and len(u) < 200:
        print(u)
print('ALL DONE')
