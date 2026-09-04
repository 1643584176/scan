# -*- coding: utf-8 -*-
"""v215 驱动: CreateSnapshot driveId IDOR 探测 + 23456 监听者识别"""
import sys, os, time, base64, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v215'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda215_probe_user.py'


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
    print('[create ok] %.0fs sid=%s' % (time.time() - t0, sid))

    inject(sid, '/vercel/sandbox/vda215_probe_user.py', open(PAY, 'rb').read())

    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda215_probe_user.py'], 90000)
    print('[run payload]', c)
    print((r or '')[:15000])

    # 检查沙箱状态 (某个变体可能触发 stop)
    time.sleep(2)
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('[status]', c)
    try:
        d = json.loads(r)
        print('status=%s snap=%s' % (d.get('sandbox', {}).get('status'), d.get('sandbox', {}).get('currentSnapshotId')))
    except Exception:
        print(r[:300])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
