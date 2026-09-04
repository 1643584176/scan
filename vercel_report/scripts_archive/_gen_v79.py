# -*- coding: utf-8 -*-
# 生成 v79 guest + 驱动 (基于 v78)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda78_guest.py', encoding='utf-8').read()
g = g.replace('vda78', 'vda79').replace('v78', 'v79').replace('V78C_DONE', 'V79C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda79_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v78.py', encoding='utf-8').read()
d = d.replace('vda78', 'vda79').replace('v78', 'v79').replace('V78', 'V79')
open(r'D:\scan\_run_v79.py', 'w', encoding='utf-8').write(d)
print('done')
