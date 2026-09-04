# -*- coding: utf-8 -*-
import io

src = io.open('skills/non-traditional-vuln-hunting/vda100_guest.py', encoding='utf-8').read()
src = src.replace('vda100', 'vda105').replace('v100', 'v105')
src = src.replace("if 'V98C_DONE' in cur or 'V99_END' in cur:",
                  "if 'V105C_DONE' in cur or 'V99_END' in cur:")
io.open('skills/non-traditional-vuln-hunting/vda105_guest.py', 'w', encoding='utf-8').write(src)

drv = io.open('_run_v104.py', encoding='utf-8').read()
drv = drv.replace('vda104_guest', 'vda105_guest').replace('vda104_probe_guest', 'vda105_probe_guest')
drv = drv.replace("NAME = 'v104'", "NAME = 'v105'")
drv = drv.replace('v104m.out', 'v105m.out')
drv = drv.replace("['run guest']", "['run guest']")
drv = drv.replace('120000', '300000')
drv = drv.replace("tail -c 26000 /vercel/sandbox/v105m.out", "tail -c 30000 /vercel/sandbox/v105m.out")
# 增加 p3 文件 tail
drv = drv.replace("""    c, r = cmd(sid, 'sh', ['-c', 'cat /vercel/sandbox/exec_probe.out 2>&1'], 20000)
    print('[probe out]', c)
    print((r or '')[:12000])""",
                  """    c, r = cmd(sid, 'sh', ['-c', 'cat /vercel/sandbox/exec_probe.out 2>&1'], 20000)
    print('[probe out]', c)
    print((r or '')[:12000])

    c, r = cmd(sid, 'sh', ['-c', 'tail -c 90000 /vercel/sandbox/v105p3.out 2>&1'], 20000)
    print('[p3 file]', c)
    print((r or '')[:90000])""")
io.open('_run_v105.py', 'w', encoding='utf-8').write(drv)
print('OK', 'vda105' in src, 'V105C_DONE' in src, '300000' in drv)
