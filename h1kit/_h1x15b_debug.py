# -*- coding: utf-8 -*-
"""h1x15b: 调试 query 字符串格式"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
i = t.find('DuplicateInfoQuery')
print('repr around:', repr(t[i-150:i+250]))
print()
# 找所有 "query " 出现位置前 60 字符的形态
cnt = 0
for m in re.finditer(r'query ', t):
    i2 = m.start()
    seg = t[max(0, i2-40):i2]
    if 'fragment' not in t[i2:i2+30]:
        cnt += 1
        if cnt <= 5:
            print(repr(seg), '>>>', repr(t[i2:i2+60]))
print('total "query " occurrences:', cnt)
