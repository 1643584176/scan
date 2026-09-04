# -*- coding: utf-8 -*-
"""v189 驱动: ExecCommand 真伪判定 - 长进程 + 双视角 ps + Remove 宿主路径"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v189'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda189_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda189_probe_guest.py'
PROBE = r'D:\scan\skills\non-traditional-vuln-hunting\vda189_userprobe.py'


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

    # 阶段 A: 用户 - ExecCommand 长进程 + ps
    inject(sid, '/vercel/sandbox/userprobe.py', open(PROBE, 'rb').read())
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/userprobe.py'], 150000)
    print('[user probe]', c)
    print((r or '')[:30000])

    # 阶段 B: guest - 宿主 ps + 特征文件检查 + 创建 rm 标记
    inject(sid, '/vercel/sandbox/vda189_guest.py', open(GUEST, 'rb').read())
    inject(sid, '/vercel/sandbox/vda189_probe_guest.py', open(PAY, 'rb').read())
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda189_guest.py'], 180000)
    print('[run guest]', c)
    print((r or '')[:30000])

    c, r = cmd(sid, 'sh', ['-c', 'cat /vercel/sandbox/v189c.out 2>&1'], 20000)
    print('[v189c.out]', c)
    print((r or '')[:40000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
