# -*- coding: utf-8 -*-
# 生成 v87 guest + 驱动 (基于 v86)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda86_guest.py', encoding='utf-8').read()
g = g.replace('vda86', 'vda87').replace('v86', 'v87').replace('V86C_DONE', 'V87C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda87_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v86.py', encoding='utf-8').read()
d = d.replace('vda86', 'vda87').replace('v86', 'v87').replace('V86', 'V87')
open(r'D:\scan\_run_v87.py', 'w', encoding='utf-8').write(d)
print('done')
