# -*- coding: utf-8 -*-
"""h1x52v: bundle 考古 ReportIntentV2 fragment 完整字段 + report_intent 查询形态"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 找 ReportIntentV2 fragment 定义
for m in re.finditer(r'ReportIntentV2(?!Fragment)', t):
    j = m.start()
    ctx = t[max(0, j-200):j+2600]
    if 'FragmentDefinition' in ctx[:600]:
        print('===== ReportIntentV2 fragment @', j)
        print(ctx[:2600].replace('\n', ' '))
        print()
        break

# report_intent 出现的所有上下文(找 query 形态: report_intent(id:) vs report_intent(report_intent_id:))
print('===== report_intent 查询形态 =====')
for m in re.finditer(r'`\s*query[^`]{0,200}report_intent', t):
    print('--- @', m.start())
    print(t[m.start():m.start()+600].replace('\n', ' ')[:600])
    print()
for m in re.finditer(r'report_intent\(id:', t):
    print('>>> id: form @', m.start())
    print(t[max(0, m.start()-300):m.start()+300].replace('\n', ' ')[:600])
    print()
