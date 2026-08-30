# -*- coding: utf-8 -*-
"""从 scanl3 输出提取关键行"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\out\scanl3_scan_local2_guest_20260829_134037.txt', 'rb').read().decode('utf-8', errors='replace')

# 打印 PHASE/rows/candidate/OPEN/chunk/PTR/DONE/ERR 行
for m in re.finditer(r'\[(\d+\.\d+)\] ([^\n]+)', data):
    ts, content = m.group(1), m.group(2)
    if re.search(r'PHASE|rows:|candidate|OPEN PORTS|chunk .* open:|PTR |DONE|ERR|target ', content):
        print(content[:400])
