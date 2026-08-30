# -*- coding: utf-8 -*-
"""驱动: 新沙箱跑 vda_cell_probe + confirm33090"""
import base64, os, sys, time, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import fresh_sandbox, cmd, api

HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'

NAME = 'vdap1'
sid = fresh_sandbox(NAME)
print('sid =', sid)

for guest, marker, outname in [
    ('vda_cell_probe_guest.py', 'VDAP_DONE', 'vdap.out'),
    ('confirm33090_guest.py', 'CFM90_DONE', 'cfm90.out'),
]:
    code = open(os.path.join(HERE, guest), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (guest, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('inject %s: %d %s' % (guest, c, r[:80]))
    time.sleep(1)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + guest], timeout_ms=90000)
    print('run %s: %d %s' % (guest, c, r[:150]))
    done = False
    for attempt in range(8):
        time.sleep(4)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + outname], timeout_ms=30000)
        if c == 200 and marker in r:
            fn = os.path.join(OUTDIR, '%s_%s.txt' % (guest.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
            open(fn, 'w', encoding='utf-8').write(r)
            print('saved ->', fn)
            done = True
            break
        print('  wait r%d status=%d' % (attempt, c))
    if not done:
        print('TIMEOUT for', guest)

# 清理
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, 'team_GIy1SZ444lspqeNbh4r8uAUg', 'prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F'))
print('cleaned up')
