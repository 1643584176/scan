# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda98_guest.py', encoding='utf-8').read()
src = src.replace('v98', 'v99').replace('V66', 'V99').replace('v66', 'v99')
io.open('skills/non-traditional-vuln-hunting/vda99_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v98.py', encoding='utf-8').read()
drv = drv.replace('vda98_guest', 'vda99_guest').replace('vda98_probe_guest', 'vda99_probe_guest')
drv = drv.replace("NAME = 'v98'", "NAME = 'v99'")
io.open('_run_v99.py', 'w', encoding='utf-8').write(drv)
print('OK guest v99 count:', src.count('v99'), '| driver v99 count:', drv.count('v99'))
