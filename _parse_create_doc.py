# -*- coding: utf-8 -*-
"""解析 Create a named sandbox 文档, 确认 networkPolicy 创建参数支持情况"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

p = r'C:\Users\lbb.LAPTOP-LU4P5L6T\.qoder\cache\projects\scan-dcb95ef8\agent-tools\cecd10e6\008f9507.txt'
txt = open(p, encoding='utf-8', errors='replace').read()
lines = txt.splitlines()

# 1. networkPolicy/firewall 相关行
print('===== networkPolicy / firewall 相关 =====')
for i, l in enumerate(lines):
    if re.search(r'networkPolicy|network-policy|deny-all|allowedDomains|allowedCIDRs|deniedCIDRs|firewall|Firewall', l):
        print('%4d: %s' % (i, l[:300]))
        print()

# 2. 请求参数列表上下文 (找到参数表格区)
print('===== 参数表格区上下文 =====')
for i, l in enumerate(lines):
    if re.search(r'Body|Request Body|Parameters|project.*string|teamId.*string', l):
        # 打印该行及附近
        for j in range(max(0, i-1), min(len(lines), i+4)):
            print('%4d: %s' % (j, lines[j][:300]))
        print('---')
