# -*- coding: utf-8 -*-
"""v186 驱动: 沙箱用户视角可达性 + guest 控制面深挖"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v186'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda186_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda186_probe_guest.py'
PROBE = r'D:\scan\skills\non-traditional-vuln-hunting\vda186_userprobe.py'


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

    # === 阶段 A: 沙箱用户视角 (无逃逸) 控制面可达性 ===
    inject(sid, '/vercel/sandbox/userprobe.py', open(PROBE, 'rb').read())
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/userprobe.py'], 60000)
    print('[user probe]', c)
    print((r or '')[:8000])

    # === 阶段 B: guest 深挖 ===
    inject(sid, '/vercel/sandbox/vda186_guest.py', open(GUEST, 'rb').read())
    inject(sid, '/vercel/sandbox/vda186_probe_guest.py', open(PAY, 'rb').read())
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda186_guest.py'], 300000)
    print('[run guest]', c)
    print((r or '')[:30000])

    c, r = cmd(sid, 'sh', ['-c', 'cat /vercel/sandbox/v186c.out 2>&1'], 20000)
    print('[v186c.out]', c)
    print((r or '')[:45000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
