# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda115_guest.py', encoding='utf-8').read()
src = src.replace('vda115', 'vda116').replace('v115', 'v116')
src = src.replace("if 'V115C_DONE' in cur", "if 'V116C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda116_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v115.py', encoding='utf-8').read()
drv = drv.replace('vda115_guest', 'vda116_guest').replace('vda115_probe_guest', 'vda116_probe_guest')
drv = drv.replace("NAME = 'v115'", "NAME = 'v116'")
drv = drv.replace('v115m.out', 'v116m.out')
drv = drv.replace('v115p3.out', 'v116p3.out')
io.open('_run_v116.py', 'w', encoding='utf-8').write(drv)
print('OK')
