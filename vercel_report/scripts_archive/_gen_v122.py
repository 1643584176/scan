# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda121_guest.py', encoding='utf-8').read()
src = src.replace('vda121', 'vda122').replace('V121C_DONE', 'V122C_DONE').replace('v121', 'v122')
io.open('skills/non-traditional-vuln-hunting/vda122_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v121.py', encoding='utf-8').read()
drv = drv.replace('vda121_guest', 'vda122_guest').replace('vda121_probe_guest', 'vda122_probe_guest')
drv = drv.replace("NAME = 'v121'", "NAME = 'v122'")
drv = drv.replace('v121m.out', 'v122m.out')
drv = drv.replace('v121p3.out', 'v122p3.out')
# v122 需要读回 descriptor 输出文件
drv = drv.replace("tail -c 90000 /vercel/sandbox/v122p3.out 2>&1", "tail -c 200000 /vercel/sandbox/v122d.out 2>&1")
io.open('_run_v122.py', 'w', encoding='utf-8').write(drv)
print('OK')
