# -*- coding: utf-8 -*-
"""h1x50g: isValidSubject + VX 报告 collection url/parse + report_id 非0 数据路径"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

for pat in [r'isValidSubject', r'class VX', r'VX=class', r'get reports\(', r'reports=\{\}']:
    for m in re.finditer(pat, t):
        j = m.start()
        ctx = t[max(0, j-800):j+800].replace('\n', ' ')
        print('=' * 20, pat, '@', j)
        print(ctx[:1600])
        print()
