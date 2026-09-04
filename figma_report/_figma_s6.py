# -*- coding: utf-8 -*-
"""script 6 完整内容 + 全部 JS 中 figma_app- 模式"""
import re, os, glob

c = open('D:/scan/figma_report/_js/app_file.html', 'r', encoding='utf-8', errors='ignore').read()
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', c, re.S)
s6 = scripts[6]
print('== script6 len', len(s6))
# 找关键内容:view 名/livegraph/websocket url
for kw in ['livegraph', 'View', 'subscribe', 'viewName', 'wss://', 'figma_app']:
    for m in list(re.finditer(r'.{70}%s.{100}' % kw, s6))[:5]:
        print(' [%s]:' % kw, m.group(0).replace('\n', ' ')[:190])
print()
print('== 所有 JS 中 figma_app- 模式 ==')
D = 'D:/scan/figma_report/_js/'
total = 0
for p in glob.glob(D + '*.min.js'):
    d = open(p, 'r', encoding='utf-8', errors='ignore').read()
    hits = re.findall(r'figma_app[\w\-\.]{0,60}', d)
    for h in set(hits):
        if '-' in h or '.' in h:
            print(os.path.basename(p), ':', h[:80])
    total += len(d)
print('total js bytes:', total)
