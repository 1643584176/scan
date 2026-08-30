# -*- coding: utf-8 -*-
"""提取 e150 中所有 J 系列摘要行, 找未完成链"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()

for i, l in enumerate(lines):
    if re.search(r'\bJ\d{3}\b', l):
        # 只打印含 结论/结果/写 的摘要行, 或含 J 编号起始的行
        print('%4d: %s' % (i, l[:600]))
        print()
