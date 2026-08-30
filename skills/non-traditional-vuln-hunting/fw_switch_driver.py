# -*- coding: utf-8 -*-
"""fw_switch_driver: allowcmp 沙箱策略切换全流程
1) resume allowcmp (allow-all) -> 跑 fw_switch (PHASE1)
2) 切 custom (httpbin.org) -> 跑 fw_switch (PHASE2)
3) 切 deny-all -> 跑 fw_switch (PHASE3)
"""
import base64, json, os, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

HERE = r'F:\scan\skills\non-traditional-vuln-hunting'
OUTDIR = r'F:\scan\skills\out'
GUEST = 'fw_switch_guest.py'
OUTF = 'fwsw.out'
MARK = 'FWSW_DONE'


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
    print('set %s:' % mode, c, r[:120], flush=True)
    time.sleep(4)


def inject_run(sid, outname):
    code = open(os.path.join(HERE, GUEST), 'rb').read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (GUEST, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('inject:', c, flush=True)
    time.sleep(1)
    # 清空旧输出
    cmd(sid, 'rm', ['-f', '/vercel/sandbox/' + outname], timeout_ms=10000)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + GUEST], timeout_ms=120000)
    print('run:', c, flush=True)
    for attempt in range(12):
        time.sleep(4)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + outname], timeout_ms=30000)
        if c == 200 and MARK in r:
            return r
        print('wait r%d status=%d' % (attempt, c), flush=True)
    return r


def main():
    sid = resume('allowcmp')
    print('sid:', sid, flush=True)
    time.sleep(2)

    print('=== PHASE1 allow-all ===', flush=True)
    r1 = inject_run(sid, 'fwsw1.out')
    fn1 = os.path.join(OUTDIR, 'allowcmp_phase1_allowall.txt')
    open(fn1, 'w', encoding='utf-8').write(r1)
    print('saved ->', fn1, flush=True)

    set_policy(sid, 'custom')
    print('=== PHASE2 custom ===', flush=True)
    r2 = inject_run(sid, 'fwsw2.out')
    fn2 = os.path.join(OUTDIR, 'allowcmp_phase2_custom.txt')
    open(fn2, 'w', encoding='utf-8').write(r2)
    print('saved ->', fn2, flush=True)

    set_policy(sid, 'deny-all')
    print('=== PHASE3 deny-all ===', flush=True)
    r3 = inject_run(sid, 'fwsw3.out')
    fn3 = os.path.join(OUTDIR, 'allowcmp_phase3_denyall.txt')
    open(fn3, 'w', encoding='utf-8').write(r3)
    print('saved ->', fn3, flush=True)

    print('=== ALL PHASES DONE ===', flush=True)


if __name__ == '__main__':
    main()
