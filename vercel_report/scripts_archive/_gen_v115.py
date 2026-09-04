# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda114_guest.py', encoding='utf-8').read()
src = src.replace('vda114', 'vda115').replace('v114', 'v115')
src = src.replace("if 'V114C_DONE' in cur", "if 'V115C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda115_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v114.py', encoding='utf-8').read()
drv = drv.replace('vda114_guest', 'vda115_guest').replace('vda114_probe_guest', 'vda115_probe_guest')
drv = drv.replace("NAME = 'v114'", "NAME = 'v115'")
drv = drv.replace('v114m.out', 'v115m.out')
drv = drv.replace('v114p3.out', 'v115p3.out')
io.open('_run_v115.py', 'w', encoding='utf-8').write(drv)
print('OK')
