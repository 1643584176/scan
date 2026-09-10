# -*- coding: utf-8 -*-
"""7435 里 explore/featured/trending/category 数据源挖掘"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

fp = r'D:\scan\figma_report\_js\7435-ce1dc6726292bd56.min.js'
data = open(fp, encoding='utf-8', errors='ignore').read()

for kw in ['explore', 'featured', 'trending', 'category', 'categories']:
    print(f'########## KW: {kw}')
    cnt = 0
    for m in re.finditer(kw, data):
        s = max(0, m.start() - 120)
        ctx = data[s:m.end() + 180]
        # 只要含有 url/api/http 的上下文
        if re.search(r'url|/api/|http|fetch|get[A-Z]', ctx):
            print(f'  pos {m.start()}:', ctx.replace('\n', ' ')[:280])
            cnt += 1
            if cnt >= 6:
                break
    if cnt == 0:
        print('  (no api-like context)')
