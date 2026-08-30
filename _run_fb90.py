# -*- coding: utf-8 -*-
"""驱动: resume scanl5 -> fb90_probe; 若 IP 非 *.64.100 池则创建新沙箱多次探测"""
import base64, os, sys, time, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd

TEAM = 'team_GIy1SZ444lspqeNbh4r8uAUg'
PROJ = 'prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F'
HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'

GUEST = 'fb90_probe_guest.py'
OUTF = 'fb90.out'
MARK = 'FB90_DONE'


def inject_run(sid, tag):
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('[%s] inject %d' % (tag, c), flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=60000)
    print('[%s] run %d' % (tag, c), flush=True)
    for attempt in range(6):
        time.sleep(3)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
        if c == 200 and MARK in r:
            fn = os.path.join(OUTDIR, '%s_%s.txt' % (GUEST.replace('.py', ''), tag))
            open(fn, 'w', encoding='utf-8').write(r)
            print('[%s] saved -> %s' % (tag, fn), flush=True)
            return r
        print('[%s] wait r%d status=%d' % (tag, attempt, c), flush=True)
    return None


# 1) resume scanl5
c, r = api('GET', '/v2/sandboxes/scanl5?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print('resume scanl5:', c, flush=True)
if c == 200:
    d = json.loads(r)
    sid = d['session']['id']
    print('scanl5 sid =', sid, flush=True)
    time.sleep(2)
    inject_run(sid, 'scanl5')

# 2) 新沙箱探测池 (最多 4 次)
for i in range(4):
    name = 'fb90x%d' % i
    try:
        c, r = api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    except Exception:
        pass
    time.sleep(1)
    c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, {'projectId': PROJ, 'name': name})
    if c != 200:
        print('create %s fail %d %s' % (name, c, r[:200]), flush=True)
        continue
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    print('[%s] sid = %s' % (name, sid), flush=True)
    time.sleep(2)
    inject_run(sid, name)
