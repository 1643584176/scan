# -*- coding: utf-8 -*-
"""D 线: custom4 驱动 - resume fwcustom1 (切回 custom) -> 跑 payload 探测"""
import base64, json, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'
GUEST = 'fw_custom4_guest.py'
OUTF = 'fwcustom4.out'
MARK = 'FWCUSTOM4_DONE'

# resume fwcustom1
c, r = api('GET', '/v2/sandboxes/fwcustom1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print('resume fwcustom1:', c, flush=True)
if c != 200:
    print('FAIL:', r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid:', sid, flush=True)

# 切回 custom 模式
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
           {'mode': 'custom', 'allowedDomains': ['httpbin.org']})
print('set custom policy:', c, r[:200], flush=True)
time.sleep(3)

code = open(os.path.join(HERE, GUEST), 'rb').read()
payload = base64.b64encode(code).decode()
inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
print('inject:', c, flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=300000)
print('run:', c, flush=True)
for attempt in range(30):
    time.sleep(6)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
    if c == 200 and MARK in r:
        fn = os.path.join(OUTDIR, 'fw_custom4_guest_result.txt')
        open(fn, 'w', encoding='utf-8').write(r)
        print('saved ->', fn, flush=True)
        break
    print('wait r%d status=%d' % (attempt, c), flush=True)
print('=== CUSTOM4 DONE ===', flush=True)
