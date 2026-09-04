# -*- coding: utf-8 -*-
"""GBK 解码 e150_tail.txt 完整内容"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
data = open(r'F:\scan\skills\non-traditional-vuln-hunting\e150_tail.txt', 'rb').read()
txt = data.decode('gbk', errors='replace')
print(txt)
