# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding='utf-8')
txt = open(r'D:\scan\v66_run.log', encoding='utf-8', errors='replace').read()
# 提取 payload 输出的所有 log 行: [ts] xxx
for m in re.finditer(r'\[17881482\d+\.\d{3}\] ([^\n]{0,300})', txt):
    print(m.group(1)[:300])
