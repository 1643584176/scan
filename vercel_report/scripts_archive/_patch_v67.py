# -*- coding: utf-8 -*-
p1 = r'D:\scan\skills\non-traditional-vuln-hunting\vda67_guest.py'
t = open(p1, encoding='utf-8').read().replace('vda66_probe_guest.py', 'vda67_probe_guest.py')
open(p1, 'w', encoding='utf-8').write(t)
p2 = r'D:\scan\_run_v67.py'
t2 = open(p2, encoding='utf-8').read().replace('vda66_probe_guest.py', 'vda67_probe_guest.py')
open(p2, 'w', encoding='utf-8').write(t2)
print('patched')
