# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda112_guest.py', encoding='utf-8').read()
src = src.replace('vda112', 'vda113').replace('v112', 'v113')
src = src.replace("if 'V112C_DONE' in cur", "if 'V113C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda113_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v112.py', encoding='utf-8').read()
drv = drv.replace('vda112_guest', 'vda113_guest').replace('vda112_probe_guest', 'vda113_probe_guest')
drv = drv.replace("NAME = 'v112'", "NAME = 'v113'")
drv = drv.replace('v112m.out', 'v113m.out')
drv = drv.replace('v112p3.out', 'v113p3.out')
io.open('_run_v113.py', 'w', encoding='utf-8').write(drv)
print('OK')
