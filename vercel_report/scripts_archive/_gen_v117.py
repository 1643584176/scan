# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda116_guest.py', encoding='utf-8').read()
src = src.replace('vda116', 'vda117').replace('V116C_DONE', 'V117C_DONE').replace('v116', 'v117')
io.open('skills/non-traditional-vuln-hunting/vda117_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v116.py', encoding='utf-8').read()
drv = drv.replace('vda116_guest', 'vda117_guest').replace('vda116_probe_guest', 'vda117_probe_guest')
drv = drv.replace("NAME = 'v116'", "NAME = 'v117'")
drv = drv.replace('v116m.out', 'v117m.out')
drv = drv.replace('v116p3.out', 'v117p3.out')
io.open('_run_v117.py', 'w', encoding='utf-8').write(drv)
print('OK')
