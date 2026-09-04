# -*- coding: utf-8 -*-
# 生成 v74 guest + 驱动 (基于 v73)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda73_guest.py', encoding='utf-8').read()
g = g.replace('vda73', 'vda74').replace('v73', 'v74')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda74_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v73.py', encoding='utf-8').read()
d = d.replace('vda73', 'vda74').replace('v73', 'v74')
open(r'D:\scan\_run_v74.py', 'w', encoding='utf-8').write(d)
print('done')
