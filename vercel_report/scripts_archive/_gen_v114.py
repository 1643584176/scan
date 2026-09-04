# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda113_guest.py', encoding='utf-8').read()
src = src.replace('vda113', 'vda114').replace('v113', 'v114')
src = src.replace("if 'V113C_DONE' in cur", "if 'V114C_DONE' in cur")
io.open('skills/non-traditional-vuln-hunting/vda114_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v113.py', encoding='utf-8').read()
drv = drv.replace('vda113_guest', 'vda114_guest').replace('vda113_probe_guest', 'vda114_probe_guest')
drv = drv.replace("NAME = 'v113'", "NAME = 'v114'")
drv = drv.replace('v113m.out', 'v114m.out')
drv = drv.replace('v113p3.out', 'v114p3.out')
io.open('_run_v114.py', 'w', encoding='utf-8').write(drv)
print('OK')
