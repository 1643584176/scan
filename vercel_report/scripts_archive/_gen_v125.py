# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda124_guest.py', encoding='utf-8').read()
src = src.replace('vda124', 'vda125').replace('V124C_DONE', 'V125C_DONE').replace('v124', 'v125')
io.open('skills/non-traditional-vuln-hunting/vda125_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v124.py', encoding='utf-8').read()
drv = drv.replace('vda124_guest', 'vda125_guest').replace('vda124_probe_guest', 'vda125_probe_guest')
drv = drv.replace("NAME = 'v124'", "NAME = 'v125'")
drv = drv.replace('v124m.out', 'v125m.out').replace('v124d.out', 'v125d.out')
io.open('_run_v125.py', 'w', encoding='utf-8').write(drv)
print('OK')
