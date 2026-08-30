# -*- coding: utf-8 -*-
"""驱动: UDP 出网三模式对照 (同一沙箱切策略 deny-all -> allow-all -> custom)
判定: 防火墙承诺拦截 outbound TCP + DNS; UDP 非 DNS (NTP/随机端口) 是否出网?"""
import base64, os, sys, time, json
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'udptest44'
GUEST = 'vda44_udp_probe_guest.py'
HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTF = 'udp_probe_%s.out'
OUTDIR = r'F:\scan\skills\out'


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
    return json.loads(r)['sandbox']['currentSessionId']


def set_policy(sid, mode):
    body = {"mode": mode}
    if mode == 'custom':
        body["allowedDomains"] = ["httpbin.org"]
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body, 60)
    print('[policy] %s -> %s %s' % (mode, c, (r or '')[:200]), flush=True)
    time.sleep(4)


def inject(sid):
    c, r = cmd(sid, 'sh', ['-c', 'mkdir -p /vercel/sandbox'], timeout_ms=15000)
    print('mkdir:', c, flush=True)
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inj = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inj], timeout_ms=30000)
    print('inject:', c, (r or '')[:200], flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'sh', ['-c', 'ls -la /vercel/sandbox/'], timeout_ms=15000)
    print('verify:', c, (r or '')[:200], flush=True)
    if GUEST not in (r or ''):
        print('INJECT FAIL - abort', flush=True)
        sys.exit(2)


def run_mode(sid, mode):
    c, r = cmd(sid, 'sh', ['-c', 'nohup python3 /vercel/sandbox/%s %s > /tmp/udp_%s_stdout.txt 2>&1 &' % (GUEST, mode, mode)], timeout_ms=15000)
    print('kick %s: %s' % (mode, c), flush=True)
    for attempt in range(20):
        time.sleep(3)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + (OUTF % mode)], timeout_ms=20000)
        if c == 200 and 'UDPPROBE_DONE' in r:
            fn = os.path.join(OUTDIR, 'udp44_%s_%s.txt' % (mode, time.strftime('%Y%m%d_%H%M%S')))
            open(fn, 'w', encoding='utf-8').write(r)
            print('saved ->', fn, flush=True)
            print(r[-1800:], flush=True)
            return fn
        if attempt in (1, 4):
            c2, r2 = cmd(sid, 'sh', ['-c', 'tail -5 /tmp/udp_%s_stdout.txt 2>/dev/null; ls -la /vercel/sandbox/' % mode], timeout_ms=20000)
            print('diag %s: %s' % (mode, (r2 or '').replace('\\n', ' ')[-350:]), flush=True)
        print('wait %s r%d status=%d | %s' % (mode, attempt, c, (r or '').replace('\\n', ' ')[-150:]), flush=True)
    return None


if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(5)
    inject(sid)
    set_policy(sid, 'deny-all')
    run_mode(sid, 'denyall')
    set_policy(sid, 'allow-all')
    run_mode(sid, 'allowall')
    set_policy(sid, 'custom')
    run_mode(sid, 'custom')
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
