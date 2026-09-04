# -*- coding: utf-8 -*-
import shutil, io

# v66 -> v67: guest + payload 文件名替换
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda66_guest.py', encoding='utf-8').read()
g = g.replace('v66', 'v67')
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda67_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v66.py', encoding='utf-8').read()
d = d.replace('v66', 'v67')
open(r'D:\scan\_run_v67.py', 'w', encoding='utf-8').write(d)
print('done')
