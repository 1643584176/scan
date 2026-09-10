# -*- coding: utf-8 -*-
"""h1x13: 从 app bundle 找 duplicate 关联字段的 GraphQL 用法"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
for kw in ['duplicate_reports', 'original_report {', 'duplicate_information', 'original_report_id']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), t)]
    print('===', kw, 'count:', len(idxs))
    for i in idxs[:4]:
        seg = t[max(0, i-300):i+300]
        print(repr(seg))
        print('---')
