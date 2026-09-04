# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda109_guest.py', encoding='utf-8').read()
src = src.replace('vda109', 'vda110').replace('v109', 'v110')
src = src.replace("if 'V109C_DONE' in cur", "if 'V110C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda110_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v109.py', encoding='utf-8').read()
drv = drv.replace('vda109_guest', 'vda110_guest').replace('vda109_probe_guest', 'vda110_probe_guest')
drv = drv.replace("NAME = 'v109'", "NAME = 'v110'")
drv = drv.replace('v109m.out', 'v110m.out')
drv = drv.replace('v109p3.out', 'v110p3.out')
io.open('_run_v110.py', 'w', encoding='utf-8').write(drv)
print('OK')
