# -*- coding: utf-8 -*-
# 生成 v88 guest + 驱动 (基于 v87)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda87_guest.py', encoding='utf-8').read()
g = g.replace('vda87', 'vda88').replace('v87', 'v88').replace('V87C_DONE', 'V88C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda88_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v87.py', encoding='utf-8').read()
d = d.replace('vda87', 'vda88').replace('v87', 'v88').replace('V87', 'V88')
open(r'D:\scan\_run_v88.py', 'w', encoding='utf-8').write(d)
print('done')
