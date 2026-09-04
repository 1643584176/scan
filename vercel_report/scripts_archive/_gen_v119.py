# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda118_guest.py', encoding='utf-8').read()
src = src.replace('vda118', 'vda119').replace('V118C_DONE', 'V119C_DONE').replace('v118', 'v119')
io.open('skills/non-traditional-vuln-hunting/vda119_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v118.py', encoding='utf-8').read()
drv = drv.replace('vda118_guest', 'vda119_guest').replace('vda118_probe_guest', 'vda119_probe_guest')
drv = drv.replace("NAME = 'v118'", "NAME = 'v119'")
drv = drv.replace('v118m.out', 'v119m.out')
drv = drv.replace('v118p3.out', 'v119p3.out')
io.open('_run_v119.py', 'w', encoding='utf-8').write(drv)
print('OK')
