# -*- coding: utf-8 -*-
"""v209 驱动: 旧签名跨沙箱重放测试"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v209'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda209_probe_user.py'


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

    inject(sid, '/vercel/sandbox/vda209_probe_user.py', open(PAY, 'rb').read())
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda209_probe_user.py'], 70000)
    print('[run payload]', c)
    print((r or '')[:8000])

    # 再确认文件
    c, r = cmd(sid, 'bash', ['-c', 'ls -la /tmp/v209_* 2>&1; echo ---; cat /tmp/v209_* 2>&1'], 15000)
    print('[files]', c)
    print((r or '')[:1500])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
