# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda106_guest.py', encoding='utf-8').read()
src = src.replace('vda106', 'vda107').replace('v106', 'v107')
src = src.replace("if 'V106C_DONE' in cur", "if 'V107C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda107_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v106.py', encoding='utf-8').read()
drv = drv.replace('vda106_guest', 'vda107_guest').replace('vda106_probe_guest', 'vda107_probe_guest')
drv = drv.replace("NAME = 'v106'", "NAME = 'v107'")
drv = drv.replace('v106m.out', 'v107m.out')
drv = drv.replace('v106p3.out', 'v107p3.out')
io.open('_run_v107.py', 'w', encoding='utf-8').write(drv)
print('OK')
