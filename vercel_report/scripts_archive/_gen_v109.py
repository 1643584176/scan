# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda108_guest.py', encoding='utf-8').read()
src = src.replace('vda108', 'vda109').replace('v108', 'v109')
src = src.replace("if 'V108C_DONE' in cur", "if 'V109C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda109_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v108.py', encoding='utf-8').read()
drv = drv.replace('vda108_guest', 'vda109_guest').replace('vda108_probe_guest', 'vda109_probe_guest')
drv = drv.replace("NAME = 'v108'", "NAME = 'v109'")
drv = drv.replace('v108m.out', 'v109m.out')
drv = drv.replace('v108p3.out', 'v109p3.out')
io.open('_run_v109.py', 'w', encoding='utf-8').write(drv)
print('OK')
