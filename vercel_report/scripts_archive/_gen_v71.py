# -*- coding: utf-8 -*-
# 生成 v71 guest + 驱动 (基于 v70, 输出双写)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda70_guest.py', encoding='utf-8').read()
g = g.replace('vda70', 'vda71').replace('v70', 'v71')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda71_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v70.py', encoding='utf-8').read()
d = d.replace('vda70', 'vda71').replace('v70', 'v71')
open(r'D:\scan\_run_v71.py', 'w', encoding='utf-8').write(d)
print('done')
