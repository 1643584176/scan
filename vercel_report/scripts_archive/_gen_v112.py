# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda111_guest.py', encoding='utf-8').read()
src = src.replace('vda111', 'vda112').replace('v111', 'v112')
src = src.replace("if 'V111C_DONE' in cur", "if 'V112C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda112_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v111.py', encoding='utf-8').read()
drv = drv.replace('vda111_guest', 'vda112_guest').replace('vda111_probe_guest', 'vda112_probe_guest')
drv = drv.replace("NAME = 'v111'", "NAME = 'v112'")
drv = drv.replace('v111m.out', 'v112m.out')
drv = drv.replace('v111p3.out', 'v112p3.out')
io.open('_run_v112.py', 'w', encoding='utf-8').write(drv)
print('OK')
