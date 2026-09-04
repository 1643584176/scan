# -*- coding: utf-8 -*-
# 生成 v82 guest + 驱动 (基于 v81)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda81_guest.py', encoding='utf-8').read()
g = g.replace('vda81', 'vda82').replace('v81', 'v82').replace('V81C_DONE', 'V82C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda82_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v81.py', encoding='utf-8').read()
d = d.replace('vda81', 'vda82').replace('v81', 'v82').replace('V81', 'V82')
open(r'D:\scan\_run_v82.py', 'w', encoding='utf-8').write(d)
print('done')
