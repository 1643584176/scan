# -*- coding: utf-8 -*-
# 生成 v90 guest + 驱动 (基于 v89)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda89_guest.py', encoding='utf-8').read()
g = g.replace('vda89', 'vda90').replace('v89', 'v90').replace('V89C_DONE', 'V90C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda90_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v89.py', encoding='utf-8').read()
d = d.replace('vda89', 'vda90').replace('v89', 'v90').replace('V89', 'V90')
open(r'D:\scan\_run_v90.py', 'w', encoding='utf-8').write(d)
print('done')
