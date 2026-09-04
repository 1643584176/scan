# -*- coding: utf-8 -*-
# 生成 v81 guest + 驱动 (基于 v80)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda80_guest.py', encoding='utf-8').read()
g = g.replace('vda80', 'vda81').replace('v80', 'v81').replace('V80C_DONE', 'V81C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda81_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v80.py', encoding='utf-8').read()
d = d.replace('vda80', 'vda81').replace('v80', 'v81').replace('V80', 'V81')
open(r'D:\scan\_run_v81.py', 'w', encoding='utf-8').write(d)
print('done')
