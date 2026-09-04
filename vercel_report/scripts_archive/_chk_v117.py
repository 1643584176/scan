# -*- coding: utf-8 -*-
import io
g = io.open('skills/non-traditional-vuln-hunting/vda117_guest.py', encoding='utf-8').read()
print('guest v117 refs:', g.count('v117'))
print('V117C_DONE:', 'V117C_DONE' in g)
print('v116 leftover:', g.count('v116'))
d = io.open('_run_v117.py', encoding='utf-8').read()
print("drv NAME ok:", "NAME = 'v117'" in d)
print('drv guest ref:', 'vda117_guest' in d, 'probe ref:', 'vda117_probe_guest' in d)
print('drv v116 leftover:', d.count('v116'))
