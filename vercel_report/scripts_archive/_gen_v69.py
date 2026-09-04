# -*- coding: utf-8 -*-
# 生成 v69 guest + 驱动 (基于 v68)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda68_guest.py', encoding='utf-8').read()
g = g.replace('vda68', 'vda69').replace('v68', 'v69')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda69_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v68.py', encoding='utf-8').read()
d = d.replace('vda68', 'vda69').replace('v68', 'v69')
open(r'D:\scan\_run_v69.py', 'w', encoding='utf-8').write(d)
print('done')
