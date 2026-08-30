# -*- coding: utf-8 -*-
"""fw_mini_switch: allowcmp 同沙箱策略切换 (allow-all -> custom -> deny-all)
每阶段跑 fw_mini_guest.py 验证 172.31.0.3:5432 可达性变化
"""
import base64, json, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'
GUEST = 'fw_mini_guest.py'
OUTF = 'fwmini.out'
MARK = 'FWMINI_DONE'


def resume(name):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (name, TEAM, PROJ))
    print('resume:', c, flush=True)
    if c != 200:
        raise RuntimeError(r[:200])
    return json.loads(r)['sandbox']['currentSessionId']


def set_policy(sid, mode):
    body = {'mode': mode}
    if mode == 'custom':
        body['allowedDomains'] = ['httpbin.org']
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
    print('set %s:' % mode, c, r[:100], flush=True)
    time.sleep(5)


def inject_run(sid, outname):
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('inject:', c, flush=True)
    time.sleep(1)
    cmd(sid, 'rm', ['-f', '/vercel/sandbox/' + outname], timeout_ms=10000)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=60000)
    print('run:', c, flush=True)
    for attempt in range(10):
        time.sleep(3)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + outname], timeout_ms=30000)
        if c == 200 and MARK in r:
            return r
        print('wait r%d status=%d' % (attempt, c), flush=True)
    return r


def phase(sid, tag, mode, outname):
    set_policy(sid, mode)
    print('=== %s (%s) ===' % (tag, mode), flush=True)
    r = inject_run(sid, outname)
    fn = os.path.join(OUTDIR, 'allowcmp_switch_%s.txt' % tag)
    open(fn, 'w', encoding='utf-8').write(r)
    print('saved ->', fn, flush=True)
    return r


def main():
    sid = resume('allowcmp')
    print('sid:', sid, flush=True)
    time.sleep(2)
    phase(sid, 'p1_allowall', 'allow-all', 'fwmini.out')
    phase(sid, 'p2_custom', 'custom', 'fwmini.out')
    phase(sid, 'p3_denyall', 'deny-all', 'fwmini.out')
    phase(sid, 'p4_custom_again', 'custom', 'fwmini.out')
    print('=== ALL DONE ===', flush=True)


if __name__ == '__main__':
    main()
