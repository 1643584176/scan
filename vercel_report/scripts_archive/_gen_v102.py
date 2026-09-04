# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda100_guest.py', encoding='utf-8').read()
src = src.replace('vda100', 'vda102').replace('v100', 'v102')
io.open('skills/non-traditional-vuln-hunting/vda102_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v100.py', encoding='utf-8').read()
drv = drv.replace('vda100_guest', 'vda102_guest').replace('vda100_probe_guest', 'vda102_probe_guest')
drv = drv.replace("NAME = 'v100'", "NAME = 'v102'")
drv = drv.replace('v100m.out', 'v102m.out')
io.open('_run_v102.py', 'w', encoding='utf-8').write(drv)
print('OK', 'vda102' in src, 'v102' in drv)
