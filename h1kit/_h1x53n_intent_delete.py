# -*- coding: utf-8 -*-
"""h1x53n: bundle 考古 ReportIntent 删除/discard/abandon mutation + me.report_intents 列表页操作"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 1. intent 相关 mutation 名全找
print('===== mutation 名含 Intent 的文档 =====')
for m in list(re.finditer(r'operation:`mutation`,name:\{kind:`Name`,value:`([A-Za-z]*)Intent', t))[:20]:
    print(m.group(1) + 'Intent')
print()
for pat in ['DeleteReportIntent', 'DiscardReportIntent', 'destroyReportIntent', 'deleteReportIntent',
            'report_intent.*delete', 'abandon', 'resetReportIntent', 'removeReportIntent']:
    hits = list(re.finditer(re.escape(pat), t))
    print(f'### {pat}: {len(hits)} hits')
    for m in hits[:4]:
        j = m.start()
        print('--- @', j)
        print(t[max(0, j-300):j+350].replace('\n', ' ')[:650])
        print()
