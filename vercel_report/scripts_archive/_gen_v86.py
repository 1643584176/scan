# -*- coding: utf-8 -*-
# 生成 v86 guest + 驱动 (基于 v85)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda85_guest.py', encoding='utf-8').read()
g = g.replace('vda85', 'vda86').replace('v85', 'v86').replace('V85C_DONE', 'V86C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda86_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v85.py', encoding='utf-8').read()
d = d.replace('vda85', 'vda86').replace('v85', 'v86').replace('V85', 'V86')
open(r'D:\scan\_run_v86.py', 'w', encoding='utf-8').write(d)
print('done')
