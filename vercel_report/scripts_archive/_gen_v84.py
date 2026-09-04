# -*- coding: utf-8 -*-
# 生成 v84: guest 基于 v83 (增量轮询), payload = 修复版 v83
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda83_guest.py', encoding='utf-8').read()
g = g.replace('vda83', 'vda84').replace('v83', 'v84').replace('V83C_DONE', 'V84C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda84_guest.py', 'w', encoding='utf-8').write(g)

p = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda83_probe_guest.py', encoding='utf-8').read()
p = p.replace('v83', 'v84').replace('V83C_DONE', 'V84C_DONE')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda84_probe_guest.py', 'w', encoding='utf-8').write(p)

d = open(r'D:\scan\_run_v83.py', encoding='utf-8').read()
d = d.replace('vda83', 'vda84').replace('v83', 'v84').replace('V83', 'V84')
open(r'D:\scan\_run_v84.py', 'w', encoding='utf-8').write(d)
print('done')
