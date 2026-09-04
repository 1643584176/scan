# -*- coding: utf-8 -*-
"""驱动: resume scanl4 -> 跑 vda3_cell_ssrf"""
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

# resume scanl4 (从快照, 若 running 则直接复用)
c, r = api('GET', '/v2/sandboxes/scanl4?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
if d['sandbox']['status'] != 'running':
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
print('inject:', c, flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=150000)
print('run:', c, flush=True)
for attempt in range(10):
    time.sleep(4)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
    if c == 200 and MARK in r:
        fn = os.path.join(OUTDIR, '%s_%s.txt' % (GUEST.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
        open(fn, 'w', encoding='utf-8').write(r)
        print('saved ->', fn, flush=True)
        break
    print('wait r%d status=%d' % (attempt, c), flush=True)
