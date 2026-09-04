# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda119_guest.py', encoding='utf-8').read()
src = src.replace('vda119', 'vda120').replace('V119C_DONE', 'V120C_DONE').replace('v119', 'v120')
io.open('skills/non-traditional-vuln-hunting/vda120_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v119.py', encoding='utf-8').read()
drv = drv.replace('vda119_guest', 'vda120_guest').replace('vda119_probe_guest', 'vda120_probe_guest')
drv = drv.replace("NAME = 'v119'", "NAME = 'v120'")
drv = drv.replace('v119m.out', 'v120m.out')
drv = drv.replace('v119p3.out', 'v120p3.out')
io.open('_run_v120.py', 'w', encoding='utf-8').write(drv)
print('OK')
