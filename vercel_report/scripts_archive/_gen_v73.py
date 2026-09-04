# -*- coding: utf-8 -*-
# 生成 v73 guest + 驱动 (基于 v72)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda72_guest.py', encoding='utf-8').read()
g = g.replace('vda72', 'vda73').replace('v72', 'v73')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda73_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v72.py', encoding='utf-8').read()
d = d.replace('vda72', 'vda73').replace('v72', 'v73')
open(r'D:\scan\_run_v73.py', 'w', encoding='utf-8').write(d)
print('done')
