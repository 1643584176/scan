# -*- coding: utf-8 -*-
# 生成 v75 guest + 驱动 (基于 v74)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda74_guest.py', encoding='utf-8').read()
g = g.replace('vda74', 'vda75').replace('v74', 'v75')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda75_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v74.py', encoding='utf-8').read()
d = d.replace('vda74', 'vda75').replace('v74', 'v75')
open(r'D:\scan\_run_v75.py', 'w', encoding='utf-8').write(d)
print('done')
