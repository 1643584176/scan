# -*- coding: utf-8 -*-
# 生成 v95 guest + 驱动 (基于 v94)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda94_guest.py', encoding='utf-8').read()
g = g.replace('vda94', 'vda95').replace('v94', 'v95').replace('V94C_DONE', 'V95C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda95_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v94.py', encoding='utf-8').read()
d = d.replace('vda94', 'vda95').replace('v94', 'v95').replace('V94', 'V95')
open(r'D:\scan\_run_v95.py', 'w', encoding='utf-8').write(d)
print('done')
