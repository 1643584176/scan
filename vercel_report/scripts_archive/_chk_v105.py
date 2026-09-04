# -*- coding: utf-8 -*-
import io
drv = io.open('_run_v105.py', encoding='utf-8').read()
print('NAME v105:', "NAME = 'v105'" in drv)
print('timeout 300000:', '300000' in drv)
print('p3 tail:', 'v105p3.out' in drv)
print('guest name:', 'vda105_guest' in drv)
print('exec_probe count:', drv.count('exec_probe.out'))
g = io.open('skills/non-traditional-vuln-hunting/vda105_guest.py', encoding='utf-8').read()
print('guest V105C_DONE:', 'V105C_DONE' in g)
print('guest done cond:', 'if \'V105C_DONE\' in cur' in g)
