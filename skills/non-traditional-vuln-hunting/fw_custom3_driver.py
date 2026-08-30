# -*- coding: utf-8 -*-
"""D 线: custom3 驱动 - custom 模式跑一遍, network-policy 切 allow-all 再跑一遍 (交叉对照)"""
import base64, json, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'
GUEST = 'fw_custom3_guest.py'
OUTF = 'fwcustom3.out'
MARK = 'FWCUSTOM3_DONE'


def inject_run(sid, tag):
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('[%s] inject %d' % (tag, c), flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=120000)
    print('[%s] run %d' % (tag, c), flush=True)
    for attempt in range(12):
        time.sleep(4)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
        if c == 200 and MARK in r:
            fn = os.path.join(OUTDIR, 'fw_custom3_%s.txt' % tag)
            open(fn, 'w', encoding='utf-8').write(r)
            print('[%s] saved -> %s' % (tag, fn), flush=True)
            return r
        print('[%s] wait r%d status=%d' % (tag, attempt, c), flush=True)
    return None


def set_policy(sid, mode):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), {'mode': mode})
    print('set_policy %s -> %d %s' % (mode, c, r[:200]), flush=True)
    time.sleep(2)
    return c


# resume fwcustom1
c, r = api('GET', '/v2/sandboxes/fwcustom1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print('resume fwcustom1:', c, flush=True)
if c != 200:
    print('FAIL:', r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid:', sid, flush=True)
time.sleep(2)

# 1) custom 模式跑
print('===== RUN 1: custom mode =====', flush=True)
inject_run(sid, 'custom')

# 2) 切 allow-all 再跑
print('===== RUN 2: allow-all (policy switch) =====', flush=True)
set_policy(sid, 'allow-all')
inject_run(sid, 'allowall')

print('=== CUSTOM3 DONE ===', flush=True)
