# -*- coding: utf-8 -*-
"""v123 驱动: 注入 + 运行 + 分批读回 descriptor 区域文件"""
import sys, os, time, json, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v123'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda123_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda123_probe_guest.py'


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

    inject(sid, '/vercel/sandbox/vda123_guest.py', open(GUEST, 'rb').read())
    inject(sid, '/vercel/sandbox/vda123_probe_guest.py', open(PAY, 'rb').read())

    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda123_guest.py'], 300000)
    print('[run guest]', c)
    print((r or '')[:30000])

    c, r = cmd(sid, 'sh', ['-c', 'tail -c 20000 /vercel/sandbox/v123m.out 2>&1'], 20000)
    print('[guest tail]', c)
    print((r or '')[:18000])

    # 动态读回所有区域文件
    c, r = cmd(sid, 'sh', ['-c', 'ls /vercel/sandbox/v123d_*.bin 2>&1'], 15000)
    print('[list regions]', c)
    print((r or '')[:3000])
    files = []
    for ln in (r or '').splitlines():
        ln = ln.strip()
        if ln.startswith('/vercel/sandbox/v123d_') and ln.endswith('.bin'):
            files.append(ln)
    print('[regions count]', len(files))

    # 分批读回 (每批 3 个文件, 每个 ~38KB)
    batch = []
    for i, fp in enumerate(files):
        batch.append(fp)
        if len(batch) >= 3:
            expr = '; '.join('echo ===%s===; cat %s' % (os.path.basename(x), x) for x in batch)
            c, r = cmd(sid, 'sh', ['-c', expr], 30000)
            print('[read %d]' % i, c)
            print((r or '')[:125000])
            batch = []
    if batch:
        expr = '; '.join('echo ===%s===; cat %s' % (os.path.basename(x), x) for x in batch)
        c, r = cmd(sid, 'sh', ['-c', expr], 30000)
        print('[read last]', c)
        print((r or '')[:125000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
