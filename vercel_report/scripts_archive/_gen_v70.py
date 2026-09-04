# -*- coding: utf-8 -*-
# 生成 v70 guest (基于 v69)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda69_guest.py', encoding='utf-8').read()
g = g.replace('vda69', 'vda70').replace('v69', 'v70')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda70_guest.py', 'w', encoding='utf-8').write(g)
print('done')
