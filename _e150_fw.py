# -*- coding: utf-8 -*-
"""提取 e150 中 networkPolicy/UDP 防火墙相关完整上下文"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e1507845_text.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
lines = txt.splitlines()

for i, l in enumerate(lines):
    if re.search(r'networkPolicy|UDP 123|deny-all|防火墙|firewall|出站|egress', l, re.I):
        print('%4d: %s' % (i, l[:600]))
        print()
