# -*- coding: utf-8 -*-
import re
for line in open(r'D:\scan\figma_report\_figma_har_analysis.txt', encoding='utf-8', errors='ignore'):
    m = re.match(r'\s*(POST|PUT)\s+(/S+)', line)
    if m:
        print(line.rstrip())
