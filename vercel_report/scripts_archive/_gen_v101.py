# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda100_guest.py', encoding='utf-8').read()
src = src.replace('vda100', 'vda101').replace('v100', 'v101')
io.open('skills/non-traditional-vuln-hunting/vda101_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v100.py', encoding='utf-8').read()
drv = drv.replace('vda100_guest', 'vda101_guest').replace('vda100_probe_guest', 'vda101_probe_guest')
drv = drv.replace("NAME = 'v100'", "NAME = 'v101'")
drv = drv.replace('v100m.out', 'v101m.out')
io.open('_run_v101.py', 'w', encoding='utf-8').write(drv)
print('OK', 'vda101' in src, 'v101' in drv)
