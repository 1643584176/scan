# -*- coding: utf-8 -*-
"""提取 pidfd_run7.log 中的 guest 输出"""
import sys, re

sys.stdout.reconfigure(encoding='utf-8')
raw = open(r'D:\scan\skills\non-traditional-vuln-hunting\pidfd_run7.log', encoding='utf-8').read()
outs = re.findall(r'"data":"(.*?)"', raw)
print('data blocks:', len(outs))
for o in outs:
    t = o.encode().decode('unicode_escape', errors='replace')
    print('-----')
    print(t[:4500])
