# -*- coding: utf-8 -*-
"""D 线: custom 模式驱动 - 创建 custom 沙箱(httpbin.org 白名单) -> 跑 fw_custom_guest.py"""
import base64, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, fresh_sandbox, TEAM, PROJ

HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'
GUEST = 'fw_custom_guest.py'
OUTF = 'fwcustom.out'
MARK = 'FWCUSTOM_DONE'

sid = fresh_sandbox('fwcustom1', network_mode='custom')
print('sid:', sid, flush=True)
time.sleep(2)

code = open(os.path.join(HERE, GUEST), 'rb').read()
payload = base64.b64encode(code).decode()
inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
print('inject:', c, flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=120000)
print('run:', c, flush=True)
for attempt in range(10):
    time.sleep(4)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
    if c == 200 and MARK in r:
        fn = os.path.join(OUTDIR, 'fw_custom_guest_result.txt')
        open(fn, 'w', encoding='utf-8').write(r)
        print('saved ->', fn, flush=True)
        break
    print('wait r%d status=%d' % (attempt, c), flush=True)
print('=== CUSTOM DONE ===', flush=True)
