# -*- coding: utf-8 -*-
"""查看 e1507845 后半段: J524/J547/J551/J558/J565 等未闭合实验的结论"""
import re

with open(r'D:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 打印从第 180 行到结尾(后半段)
for i in range(180, len(lines)):
    t = lines[i].strip()
    if len(t) < 30:
        continue
    print('%4d: %s' % (i, t[:600]))
    print()
