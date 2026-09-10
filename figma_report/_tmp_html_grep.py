# -*- coding: utf-8 -*-
"""临时: 在 _r26_file_page.html 中提取编辑器入口线索"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

html = open(r'D:\scan\figma_report\_r26_file_page.html', encoding='utf-8', errors='replace').read()
print('len:', len(html))

for pat in (r'https://www\.figma\.com/design/[^"\\ <]{5,100}',
            r'https://www\.figma\.com/make/[^"\\ <]{5,100}',
            r'https://www\.figma\.com/proto/[^"\\ <]{5,100}'):
    hits = list(dict.fromkeys(re.findall(pat, html)))[:8]
    print(f'-- {pat[:40]}... -> {hits}')

for kw in ('Open in Figma', 'Duplicate', 'fileKey', 'file_key', 'hub_file_key', 'open_in_figma', 'key":"'):
    idxs = [m.start() for m in re.finditer(re.escape(kw), html)][:5]
    print(f'-- kw {kw!r}: {len(idxs)}')
    for i0 in idxs[:3]:
        seg = html[max(0,i0-90):i0+140].replace('\n', ' ')
        print(f'     ...{seg}...')
