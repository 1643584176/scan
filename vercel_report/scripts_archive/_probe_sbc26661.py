# -*- coding: utf-8 -*-
import re
data = open(r'D:\scan\_run_v183_out.txt', encoding='utf-8', errors='replace').read()
# 找 SBC 26661 相关行
for m in re.finditer(r'SBC[^"]*26661[^"]*', data):
    print(repr(m.group(0))[:500])
    print()
# 也找 CELLD 26661
for m in re.finditer(r'CELLD[^"]*26661[^"]*', data):
    print(repr(m.group(0))[:500])
    print()
