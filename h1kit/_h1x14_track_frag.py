# -*- coding: utf-8 -*-
"""h1x14: 追踪 ReportIdAndStateItemReport fragment 的使用位置(哪个 query/页面)"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 1. fragment 定义附近
for m in re.finditer(r'ReportIdAndStateItemReport', t):
    i = m.start()
    print('=== occurrence @', i)
    print(repr(t[max(0,i-400):i+400]))
    print()

# 2. 找使用这个 fragment 的 operation 名称(向前找 operation:`query XXX` 或 mutation)
for m in re.finditer(r'ReportIdAndStateItemReport', t):
    i = m.start()
    head = t[max(0,i-4000):i]
    ops = re.findall(r'(?:query|mutation)\s+([A-Za-z0-9_]+)', head)
    print('candidate ops before:', ops[-6:] if ops else [])
