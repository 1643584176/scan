# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda110_guest.py', encoding='utf-8').read()
src = src.replace('vda110', 'vda111').replace('v110', 'v111')
src = src.replace("if 'V110C_DONE' in cur", "if 'V111C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda111_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v110.py', encoding='utf-8').read()
drv = drv.replace('vda110_guest', 'vda111_guest').replace('vda110_probe_guest', 'vda111_probe_guest')
drv = drv.replace("NAME = 'v110'", "NAME = 'v111'")
drv = drv.replace('v110m.out', 'v111m.out')
drv = drv.replace('v110p3.out', 'v111p3.out')
io.open('_run_v111.py', 'w', encoding='utf-8').write(drv)
print('OK')
