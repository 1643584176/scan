# -*- coding: utf-8 -*-
"""驱动: resume scanl4 + 对照新沙箱, 跑 vda2_probe"""
import base64, os, sys, time, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, fresh_sandbox

TEAM = 'team_GIy1SZ444lspqeNbh4r8uAUg'
PROJ = 'prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F'
HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'

GUEST = 'vda2_probe_guest.py'
OUTF = 'v2p.out'
MARK = 'V2P_DONE'


def run_on(sid, tag):
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('[%s] inject: %d' % (tag, c), flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=90000)
    print('[%s] run: %d' % (tag, c), flush=True)
    for attempt in range(8):
        time.sleep(4)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
        if c == 200 and MARK in r:
            fn = os.path.join(OUTDIR, '%s_%s_%s.txt' % (GUEST.replace('.py', ''), tag, time.strftime('%Y%m%d_%H%M%S')))
            open(fn, 'w', encoding='utf-8').write(r)
            print('[%s] saved -> %s' % (tag, fn), flush=True)
            return r
        print('[%s] wait r%d status=%d' % (tag, attempt, c), flush=True)
    return None


# 1) resume scanl4
print('=== resume scanl4 ===', flush=True)
c, r = api('GET', '/v2/sandboxes/scanl4?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print('resume:', c, flush=True)
print(r[:800], flush=True)
if c == 200:
    d = json.loads(r)
    sid = d['session']['id']
    print('scanl4 resumed sid =', sid, flush=True)
    time.sleep(3)
    run_on(sid, 'resumed')

# 2) 对照新沙箱
print('=== fresh sandbox ctrl ===', flush=True)
sid2 = fresh_sandbox('vdap2')
print('ctrl sid =', sid2, flush=True)
time.sleep(2)
run_on(sid2, 'fresh')
