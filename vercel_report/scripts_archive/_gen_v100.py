# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda99_guest.py', encoding='utf-8').read()
src = src.replace('vda99', 'vda100').replace('v99', 'v100')
# 轮询窗口 60 -> 300s, 间隔 1 -> 0.3s, 去掉 inject 后 sleep(1)
src = src.replace('while t_wait < 60 and not done:', 'while t_wait < 300 and not done:')
src = src.replace('time.sleep(1)\n        t_wait += 1', 'time.sleep(0.3)\n        t_wait += 1')
io.open('skills/non-traditional-vuln-hunting/vda100_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v99.py', encoding='utf-8').read()
drv = drv.replace('vda99_guest', 'vda100_guest').replace('vda99_probe_guest', 'vda100_probe_guest')
drv = drv.replace("NAME = 'v99'", "NAME = 'v100'")
drv = drv.replace('v99m.out', 'v100m.out')
drv = drv.replace('time.sleep(1)\n', '')
io.open('_run_v100.py', 'w', encoding='utf-8').write(drv)
print('OK', 'vda100' in src, 'v100' in drv)
