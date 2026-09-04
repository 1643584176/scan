# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda125_guest.py', encoding='utf-8').read()
src = src.replace('vda125', 'vda126').replace('V125C_DONE', 'V126C_DONE').replace('v125', 'v126')
io.open('skills/non-traditional-vuln-hunting/vda126_guest.py', 'w', encoding='utf-8').write(src)

probe = io.open('skills/non-traditional-vuln-hunting/vda125_probe_guest.py', encoding='utf-8').read()
probe = probe.replace('vda125', 'vda126').replace('V125C_DONE', 'V126C_DONE').replace('v125', 'v126')
io.open('skills/non-traditional-vuln-hunting/vda126_probe_guest.py', 'w', encoding='utf-8').write(probe)

drv = io.open('_run_v125.py', encoding='utf-8').read()
drv = drv.replace('vda125_guest', 'vda126_guest').replace('vda125_probe_guest', 'vda126_probe_guest')
drv = drv.replace("NAME = 'v125'", "NAME = 'v126'")
drv = drv.replace('v125m.out', 'v126m.out').replace('v125d.out', 'v126d.out')
io.open('_run_v126.py', 'w', encoding='utf-8').write(drv)
print('OK')
