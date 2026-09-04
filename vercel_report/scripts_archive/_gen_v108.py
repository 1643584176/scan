# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda107_guest.py', encoding='utf-8').read()
src = src.replace('vda107', 'vda108').replace('v107', 'v108')
src = src.replace("if 'V107C_DONE' in cur", "if 'V108C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda108_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v107.py', encoding='utf-8').read()
drv = drv.replace('vda107_guest', 'vda108_guest').replace('vda107_probe_guest', 'vda108_probe_guest')
drv = drv.replace("NAME = 'v107'", "NAME = 'v108'")
drv = drv.replace('v107m.out', 'v108m.out')
drv = drv.replace('v107p3.out', 'v108p3.out')
io.open('_run_v108.py', 'w', encoding='utf-8').write(drv)
print('OK')
