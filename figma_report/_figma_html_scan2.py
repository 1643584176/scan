# -*- coding: utf-8 -*-
"""app_file.html 全量 script 引用 + INITIAL_OPTIONS 关键字段"""
import re, html as H

c = open('D:/scan/figma_report/_js/app_file.html', 'r', encoding='utf-8', errors='ignore').read()
print('html len', len(c))

# 1. 所有 script src
print('== script src ==')
seen = set()
for m in re.finditer(r'<script[^>]*src="([^"]+)"', c):
    u = H.unescape(m.group(1))
    if u not in seen:
        seen.add(u)
        print(' ', u[:150])

# 2. 内联脚本数量
inl = re.findall(r'<script(?![^>]*src)[^>]*>(.{0,200})', c, re.S)
print('inline scripts:', len(inl))

# 3. INITIAL_OPTIONS 关键字段
print('== INITIAL_OPTIONS keys ==')
iom = re.search(r'window\.INITIAL_OPTIONS\s*=\s*({.*?});', c, re.S)
if iom:
    s = iom.group(1)
    print('len', len(s))
    for m in re.finditer(r'"([a-z_0-9]+)"\s*:', s):
        pass
    keys = re.findall(r'"([a-z_0-9]{3,40})"\s*:', s)
    from collections import Counter
    for k, v in Counter(keys).most_common(60):
        print('  ', k)
else:
    print('  not found, searching variants...')
    for m in re.finditer(r'INITIAL_OPTIONS.{0,120}', c):
        print('  ctx:', m.group(0)[:130])
        if m.start() > 500000:
            break
