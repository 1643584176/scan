# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda100_guest.py', encoding='utf-8').read()
src = src.replace('vda100', 'vda104').replace('v100', 'v104')
io.open('skills/non-traditional-vuln-hunting/vda104_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v100.py', encoding='utf-8').read()
drv = drv.replace('vda100_guest', 'vda104_guest').replace('vda100_probe_guest', 'vda104_probe_guest')
drv = drv.replace("NAME = 'v100'", "NAME = 'v104'")
drv = drv.replace('v100m.out', 'v104m.out')
io.open('_run_v104.py', 'w', encoding='utf-8').write(drv)
print('OK', 'vda104' in src, 'v104' in drv)
