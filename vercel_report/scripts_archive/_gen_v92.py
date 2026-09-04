# -*- coding: utf-8 -*-
# 生成 v92 guest + 驱动 (基于 v91)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda91_guest.py', encoding='utf-8').read()
g = g.replace('vda91', 'vda92').replace('v91', 'v92').replace('V91C_DONE', 'V92C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda92_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v91.py', encoding='utf-8').read()
d = d.replace('vda91', 'vda92').replace('v91', 'v92').replace('V91', 'V92')
open(r'D:\scan\_run_v92.py', 'w', encoding='utf-8').write(d)
print('done')
