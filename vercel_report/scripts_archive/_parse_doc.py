# -*- coding: utf-8 -*-
"""解析 Vercel Update network policy API 文档"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

p = r'C:\Users\lbb.LAPTOP-LU4P5L6T\.qoder\cache\projects\scan-dcb95ef8\agent-tools\cecd10e6\f70bb7c9.txt'
txt = open(p, encoding='utf-8', errors='replace').read()
lines = txt.splitlines()
for i, l in enumerate(lines):
    if re.search(r'PATCH|PUT|/v2/sandboxes|network-policy|deny-all|allowedDomains|allowedCIDRs|deniedCIDRs|mode|custom|request body|example', l, re.I):
        print('%4d: %s' % (i, l[:250]))
