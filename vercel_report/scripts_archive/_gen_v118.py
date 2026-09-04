# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda117_guest.py', encoding='utf-8').read()
src = src.replace('vda117', 'vda118').replace('V117C_DONE', 'V118C_DONE').replace('v117', 'v118')
io.open('skills/non-traditional-vuln-hunting/vda118_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v117.py', encoding='utf-8').read()
drv = drv.replace('vda117_guest', 'vda118_guest').replace('vda117_probe_guest', 'vda118_probe_guest')
drv = drv.replace("NAME = 'v117'", "NAME = 'v118'")
drv = drv.replace('v117m.out', 'v118m.out')
drv = drv.replace('v117p3.out', 'v118p3.out')
io.open('_run_v118.py', 'w', encoding='utf-8').write(drv)
print('OK')
