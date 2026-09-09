# -*- coding: utf-8 -*-
"""h1x52o: ①bundle 考古 duplicate_information/original_report 前端调用 ②类型字段 introspect"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

print('===== 1. bundle 考古 =====')
for pat in [r'duplicate_information', r'original_report', r'duplicates_must_have', r'duplicate_suggestions', r'ReportDuplicateInformation']:
    cnt = 0
    for m in re.finditer(pat, t):
        j = m.start()
        ctx = t[max(0, j-250):j+350].replace('\n', ' ')
        print('=' * 15, pat, '@', j)
        print(ctx[:600])
        cnt += 1
        if cnt >= 4:
            break
    print()
