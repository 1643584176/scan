# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda100_guest.py', encoding='utf-8').read()
src = src.replace('vda100', 'vda103').replace('v100', 'v103')
io.open('skills/non-traditional-vuln-hunting/vda103_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v100.py', encoding='utf-8').read()
drv = drv.replace('vda100_guest', 'vda103_guest').replace('vda100_probe_guest', 'vda103_probe_guest')
drv = drv.replace("NAME = 'v100'", "NAME = 'v103'")
drv = drv.replace('v100m.out', 'v103m.out')
io.open('_run_v103.py', 'w', encoding='utf-8').write(drv)
print('OK', 'vda103' in src, 'v103' in drv)
