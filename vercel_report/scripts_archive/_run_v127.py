# -*- coding: utf-8 -*-
"""v127 驱动: cell.sock 决定性验证 (直接 guest, 不走 vda/containerd 链)"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox

NAME = 'v127'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\v127p.py'


def run(sid, command, args, timeout_ms=60000, sudo=False):
    body = {"command": command, "args": args, "wait": True, "logs": True,
            "timeout": timeout_ms}
    if sudo:
        body["sudo"] = True
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM), body,
               timeout=timeout_ms / 1000 + 30)
    return c, r


def main():
    t0 = time.time()
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    sid = fresh_sandbox(NAME)
    print('[create ok] %.0fs' % (time.time() - t0))

    b64 = base64.b64encode(open(PAY, 'rb').read()).decode()
    s = "import base64;open('/vercel/sandbox/v127p.py','wb').write(base64.b64decode('%s'))" % b64
    c, r = run(sid, 'python3', ['-c', s], 60000)
    print('[inject]', c)

    c, r = run(sid, 'python3', ['/vercel/sandbox/v127p.py'], 240000, sudo=True)
    print('[run sudo]', c)
    print((r or '')[:30000])

    c, r = run(sid, 'sh', ['-c', 'cat /vercel/sandbox/v127.out 2>&1'], 20000)
    print('[v127.out]', c)
    print((r or '')[:30000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
