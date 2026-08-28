# -*- coding: utf-8 -*-
"""提取 494b74ea 段 145-158 全文,找 pidfd 实验代码细节"""
import sys

sys.stdout.reconfigure(encoding='utf-8')
lines = open(r'D:\scan\skills\non-traditional-vuln-hunting\494b74ea_text.txt', encoding='utf-8').readlines()
for i in range(145, min(159, len(lines))):
    print('== seg %d ==' % i)
    print(lines[i].strip())
    print()
