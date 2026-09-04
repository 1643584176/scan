# -*- coding: utf-8 -*-
"""v190 驱动: guest-A 控制面深挖+创建标记 -> 用户 Remove -> guest-C 验证"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v190'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda190_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda190_probe_guest.py'
PROBE = r'D:\scan\skills\non-traditional-vuln-hunting\vda190_userprobe.py'
CHECK = r'D:\scan\skills\non-traditional-vuln-hunting\vda190_check_guest.py'
GUEST2 = r'D:\scan\skills\non-traditional-vuln-hunting\vda190_guest2.py'
CHECKG = r'D:\scan\skills\non-traditional-vuln-hunting\vda190_check_guest2.py'


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

    # 阶段 A: guest 控制面深挖 + 创建宿主标记
    inject(sid, '/vercel/sandbox/vda190_guest.py', open(GUEST, 'rb').read())
    inject(sid, '/vercel/sandbox/vda190_probe_guest.py', open(PAY, 'rb').read())
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda190_guest.py'], 240000)
    print('[guest A]', c)
    print((r or '')[:15000])
    c, r = cmd(sid, 'sh', ['-c', 'cat /vercel/sandbox/v190c.out 2>&1'], 20000)
    print('[v190c.out A]', c)
    print((r or '')[:40000])

    # 阶段 B: 用户 Remove 宿主标记
    inject(sid, '/vercel/sandbox/userprobe.py', open(PROBE, 'rb').read())
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/userprobe.py'], 60000)
    print('[user probe]', c)
    print((r or '')[:15000])

    # 阶段 C: guest 验证标记是否被删 (payload 覆盖到 v190_payload.py 同名路径)
    inject(sid, '/vercel/sandbox/vda190_check_guest.py', open(CHECK, 'rb').read())
    inject(sid, '/vercel/sandbox/v190_payload.py', open(CHECK, 'rb').read())
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda190_check_guest.py'], 180000)
    print('[guest C]', c)
    print((r or '')[:15000])
    c, r = cmd(sid, 'sh', ['-c', 'cat /vercel/sandbox/v190c2.out 2>&1'], 20000)
    print('[v190c2.out]', c)
    print((r or '')[:20000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
