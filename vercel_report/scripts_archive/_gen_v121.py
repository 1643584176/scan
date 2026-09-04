# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda120_guest.py', encoding='utf-8').read()
src = src.replace('vda120', 'vda121').replace('V120C_DONE', 'V121C_DONE').replace('v120', 'v121')
io.open('skills/non-traditional-vuln-hunting/vda121_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v120.py', encoding='utf-8').read()
drv = drv.replace('vda120_guest', 'vda121_guest').replace('vda120_probe_guest', 'vda121_probe_guest')
drv = drv.replace("NAME = 'v120'", "NAME = 'v121'")
drv = drv.replace('v120m.out', 'v121m.out')
drv = drv.replace('v120p3.out', 'v121p3.out')
io.open('_run_v121.py', 'w', encoding='utf-8').write(drv)
print('OK')
