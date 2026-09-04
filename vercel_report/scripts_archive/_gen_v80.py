# -*- coding: utf-8 -*-
# 生成 v80 guest + 驱动 (基于 v79)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda79_guest.py', encoding='utf-8').read()
g = g.replace('vda79', 'vda80').replace('v79', 'v80').replace('V79C_DONE', 'V80C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda80_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v79.py', encoding='utf-8').read()
d = d.replace('vda79', 'vda80').replace('v79', 'v80').replace('V79', 'V80')
open(r'D:\scan\_run_v80.py', 'w', encoding='utf-8').write(d)
print('done')
