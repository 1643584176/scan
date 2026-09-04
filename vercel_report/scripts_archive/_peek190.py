# -*- coding: utf-8 -*-
"""提取 v190 运行输出中阶段 A 的 v190c.out 内容"""
import re

data = open(r'D:\scan\_run_v190_out.txt', encoding='utf-8', errors='replace').read()
# 找 v190c.out cat 后的 data 行
for m in re.finditer(r'\[v190c\.out A\][^\n]*\n(.*?)(?=\[user probe\]|\n\[)', data, re.S):
    print(m.group(1)[:30000])
    break
