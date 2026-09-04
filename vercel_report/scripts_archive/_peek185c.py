# -*- coding: utf-8 -*-
"""从 v185 输出提取 cell.sock (CELLD) 的 ContainersService/DrivesService 准确方法"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
data = open(r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\agent-tools\9aa693e0\4b2fe9d7.txt',
            encoding='utf-8', errors='replace').read()

for m in re.finditer(r'CELLD METHODS\(\d+\): ([^\n]{0,4000})', data):
    print('CELLD METHODS:', m.group(1)[:3000])
    break
for m in re.finditer(r'CELLD SERVICES\(\d+\): ([^\n]{0,2000})', data):
    print('CELLD SVCS:', m.group(1)[:2000])
    break
# HIT 精确路径
seen = set()
for m in re.finditer(r'HIT cell ([^\s]+) -> ([A-Z0-9 /]+)', data):
    k = m.group(1)
    if k not in seen:
        seen.add(k)
        print('HIT', k, m.group(2)[:40])
