# -*- coding: utf-8 -*-
# 生成 v77 guest + 驱动 (基于 v76)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda76_guest.py', encoding='utf-8').read()
g = g.replace('vda76', 'vda77').replace('v76', 'v77').replace('V76C_DONE', 'V77C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda77_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v76.py', encoding='utf-8').read()
d = d.replace('vda76', 'vda77').replace('v76', 'v77').replace('V76', 'V77')
open(r'D:\scan\_run_v77.py', 'w', encoding='utf-8').write(d)
print('done')
