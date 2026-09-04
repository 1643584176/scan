# -*- coding: utf-8 -*-
# 生成 v68 guest + 驱动 (基于 v67, 修正 vda 前缀问题)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda67_guest.py', encoding='utf-8').read()
g = g.replace('vda67', 'vda68').replace('v67', 'v68')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda68_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v67.py', encoding='utf-8').read()
d = d.replace('vda67', 'vda68').replace('v67', 'v68')
open(r'D:\scan\_run_v68.py', 'w', encoding='utf-8').write(d)
print('done')
