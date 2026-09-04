# -*- coding: utf-8 -*-
# 生成 v91 guest + 驱动 (基于 v90)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda90_guest.py', encoding='utf-8').read()
g = g.replace('vda90', 'vda91').replace('v90', 'v91').replace('V90C_DONE', 'V91C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda91_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v90.py', encoding='utf-8').read()
d = d.replace('vda90', 'vda91').replace('v90', 'v91').replace('V90', 'V91')
open(r'D:\scan\_run_v91.py', 'w', encoding='utf-8').write(d)
print('done')
