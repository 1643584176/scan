# -*- coding: utf-8 -*-
"""提取 v185 运行输出中的 HIT 和方法名"""
import re

data = open(r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\agent-tools\9aa693e0\4b2fe9d7.txt',
             encoding='utf-8', errors='replace').read()
# HIT 行
for m in re.finditer(r'HIT [^\n]+', data):
    print(m.group(0)[:600])
print('---METHODS---')
seen = set()
for m in re.finditer(r'(SBC|SBI|CELLD) METHODS\([^)]*\): ([^\n]+)', data):
    if m.group(2) not in seen:
        seen.add(m.group(2))
        print('%s: %s' % (m.group(1), m.group(2)[:1500]))
