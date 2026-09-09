# -*- coding: utf-8 -*-
"""解析 explore SSR HTML,提取真实 community 资源实例"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\figma_report\_p93_explore.html', encoding='utf-8', errors='ignore').read()

# window.__ 数据 key
for m in re.finditer(r'window\.__([A-Za-z_]+)', t):
    print('KEY:', m.group(1))
print('---')

# 找社区资源页 URL 形态 /community/{type}/{id} 或资源 JSON
for m in re.finditer(r'/community/(?:file|plugin|widget|make|template|app|tool|skill)/([A-Za-z0-9_\-]{6,40})', t):
    print('RES URL:', m.group(0)[:80])
    if m.start() > 100000:
        break
