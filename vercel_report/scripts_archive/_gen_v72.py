# -*- coding: utf-8 -*-
# 生成 v72 guest + 驱动 (基于 v71)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda71_guest.py', encoding='utf-8').read()
g = g.replace('vda71', 'vda72').replace('v71', 'v72')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda72_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v71.py', encoding='utf-8').read()
d = d.replace('vda71', 'vda72').replace('v71', 'v72')
open(r'D:\scan\_run_v72.py', 'w', encoding='utf-8').write(d)
print('done')
