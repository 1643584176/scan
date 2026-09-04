# -*- coding: utf-8 -*-
# 生成 v94 guest + 驱动 (基于 v93)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda93_guest.py', encoding='utf-8').read()
g = g.replace('vda93', 'vda94').replace('v93', 'v94').replace('V93C_DONE', 'V94C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda94_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v93.py', encoding='utf-8').read()
d = d.replace('vda93', 'vda94').replace('v93', 'v94').replace('V93', 'V94')
open(r'D:\scan\_run_v94.py', 'w', encoding='utf-8').write(d)
print('done')
