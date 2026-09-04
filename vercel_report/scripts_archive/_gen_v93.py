# -*- coding: utf-8 -*-
# 生成 v93 guest + 驱动 (基于 v92)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda92_guest.py', encoding='utf-8').read()
g = g.replace('vda92', 'vda93').replace('v92', 'v93').replace('V92C_DONE', 'V93C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda93_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v92.py', encoding='utf-8').read()
d = d.replace('vda92', 'vda93').replace('v92', 'v93').replace('V92', 'V93')
open(r'D:\scan\_run_v93.py', 'w', encoding='utf-8').write(d)
print('done')
