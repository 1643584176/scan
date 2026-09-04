# -*- coding: utf-8 -*-
# 生成 v85 guest + 驱动 (基于 v84)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda84_guest.py', encoding='utf-8').read()
g = g.replace('vda84', 'vda85').replace('v84', 'v85').replace('V84C_DONE', 'V85C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda85_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v84.py', encoding='utf-8').read()
d = d.replace('vda84', 'vda85').replace('v84', 'v85').replace('V84', 'V85')
open(r'D:\scan\_run_v85.py', 'w', encoding='utf-8').write(d)
print('done')
