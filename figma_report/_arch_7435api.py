# -*- coding: utf-8 -*-
"""7435 chunk 内全部 /api/ 模板 URL"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\figma_report\_js\7435-ce1dc6726292bd56.min.js', encoding='utf-8', errors='ignore').read()
# url`/api/...` 模板
for m in re.finditer(r'url`(/api/[^`]{3,90})`', data):
    s = max(0, m.start()-100)
    print('TPL:', m.group(1))
    print('  ctx:', data[s:m.start()].replace('\n', ' ')[-120:])
# follow 相关
for kw in ['follow', 'Follow']:
    for m in list(re.finditer(kw, data))[:10]:
        print(f'== {kw} @{m.start()}:', data[max(0,m.start()-150):m.end()+150].replace('\n', ' ')[:300])
        print()
