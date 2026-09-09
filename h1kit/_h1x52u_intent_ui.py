# -*- coding: utf-8 -*-
"""h1x52u: bundle 搜 resumeOrCreateReportIntent 触发点 + intent state 值 + mutation input 结构"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

print('===== resumeOrCreate 组件/触发点 =====')
for pat in ['resumeOrCreateReportIntent', 'reportIntentId', 'ReportIntentState', 'intentId']:
    hits = list(re.finditer(pat, t))
    print(f'\n### {pat}: {len(hits)} hits')
    for m in hits[:5]:
        j = m.start()
        print('--- @', j)
        print(t[max(0, j-200):j+300].replace('\n', ' ')[:500])
        print()
