# -*- coding: utf-8 -*-
"""h1x50f: report_id 变化行为 + subjects 数据来源 + GET /bugs 请求构造细节"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 1) onlyReportIdChanged 上下文:report_id 变化触发什么
for m in re.finditer(r'onlyReportIdChanged', t):
    j = m.start()
    ctx = t[max(0, j-500):j+500].replace('\n', ' ')
    print('=' * 20, 'onlyReportIdChanged @', j)
    print(ctx[:1000])
print()

# 2) subjects 注入点:搜 "subjects" 与 url/fetch/load 相邻(数据来源请求)
for m in re.finditer(r'subjects', t):
    j = m.start()
    ctx = t[max(0, j-300):j+300].replace('\n', ' ')
    if re.search(r'(fetch|url|load|ajax|JSON|bootstrap|api|\.get\(|\.post\(|collection)', ctx):
        print('=' * 20, 'subjects @', j)
        print(ctx[:600])
