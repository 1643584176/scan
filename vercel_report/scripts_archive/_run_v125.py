# -*- coding: utf-8 -*-
"""v124 驱动"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v125'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda125_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda125_probe_guest.py'


def inject(sid, dst, content):
    b64 = base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode()
    s = "import base64;open('%s','wb').write(base64.b64decode('%s'))" % (dst, b64)
    c, r = cmd(sid, 'python3', ['-c', s], 60000)
    print('[inject %s]' % dst, c)
    return c


def main():
    t0 = time.time()
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    sid = fresh_sandbox(NAME)
    print('[create ok] %.0fs' % (time.time() - t0))

    inject(sid, '/vercel/sandbox/vda125_guest.py', open(GUEST, 'rb').read())
    inject(sid, '/vercel/sandbox/vda125_probe_guest.py', open(PAY, 'rb').read())

    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda125_guest.py'], 300000)
    print('[run guest]', c)
    print((r or '')[:20000])

    c, r = cmd(sid, 'sh', ['-c', 'tail -c 20000 /vercel/sandbox/v125m.out 2>&1'], 20000)
    print('[guest tail]', c)
    print((r or '')[:18000])

    c, r = cmd(sid, 'sh', ['-c', 'tail -c 100000 /vercel/sandbox/v125d.out 2>&1'], 30000)
    print('[desc out]', c)
    print((r or '')[:100000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
