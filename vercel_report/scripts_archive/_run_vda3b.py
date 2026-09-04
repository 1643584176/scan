# -*- coding: utf-8 -*-
"""驱动 v2: resume scanl4 -> 注入 vda3 -> 执行 -> 拉取 (全程一个 session)"""
import base64, os, sys, time, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd

TEAM = 'team_GIy1SZ444lspqeNbh4r8uAUg'
PROJ = 'prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F'
HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'

GUEST = 'vda3_cell_ssrf_guest.py'
OUTF = 'v3p.out'
MARK = 'V3P_DONE'

# 强制 resume 新 session
c, r = api('GET', '/v2/sandboxes/scanl4?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print('resume:', c, flush=True)
if c != 200:
    print(r[:500], flush=True)
    sys.exit(1)
d = json.loads(r)
sid = d['session']['id']
print('sid =', sid, flush=True)
time.sleep(2)

code = open(os.path.join(HERE, GUEST), 'rb').read()
payload = base64.b64encode(code).decode()
inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
print('inject:', c, r[:80], flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=170000)
print('run:', c, flush=True)
for attempt in range(12):
    time.sleep(3)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
    if c == 200 and MARK in r:
        fn = os.path.join(OUTDIR, '%s_%s.txt' % (GUEST.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
        open(fn, 'w', encoding='utf-8').write(r)
        print('saved ->', fn, flush=True)
        break
    print('wait r%d status=%d' % (attempt, c), flush=True)
    time.sleep(2)
