# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda105_guest.py', encoding='utf-8').read()
src = src.replace('vda105', 'vda106').replace('v105', 'v106')
src = src.replace("if 'V105C_DONE' in cur", "if 'V106C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda106_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v105.py', encoding='utf-8').read()
drv = drv.replace('vda105_guest', 'vda106_guest').replace('vda105_probe_guest', 'vda106_probe_guest')
drv = drv.replace("NAME = 'v105'", "NAME = 'v106'")
drv = drv.replace('v105m.out', 'v106m.out')
drv = drv.replace('v105p3.out', 'v106p3.out')
io.open('_run_v106.py', 'w', encoding='utf-8').write(drv)
print('OK')
