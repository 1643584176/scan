# -*- coding: utf-8 -*-
"""v197 驱动: raw socket 抓包观测 CreateSnapshot 上传外发
阶段1: guest 抓包 (85s)
阶段2: 用户触发 CreateSnapshot x2 (SYN + DNS 变体)
阶段3: stopped -> resume -> cat 抓包日志"""
import sys, os, time, base64, json, uuid
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v197'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda197_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda197_probe_guest.py'
USERP = r'D:\scan\skills\non-traditional-vuln-hunting\vda197_user.py'


def inject(sid, dst, content):
    b64 = base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode()
    s = "import base64;open('%s','wb').write(base64.b64decode('%s'))" % (dst, b64)
    c, r = cmd(sid, 'python3', ['-c', s], 60000)
    print('[inject %s]' % dst, c)
    return c


def get_status():
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        j = json.loads(r)
        sb = j.get('sandbox', j)
        return sb.get('status'), sb.get('currentSnapshotId')
    except Exception:
        return None, (r or '')[:100]


def main():
    t0 = time.time()
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    sid = fresh_sandbox(NAME)
    print('[create ok] %.0fs' % (time.time() - t0))

    inject(sid, '/vercel/sandbox/vda197_guest.py', open(GUEST, 'rb').read())
    inject(sid, '/vercel/sandbox/vda197_probe_guest.py', open(PAY, 'rb').read())
    inject(sid, '/vercel/sandbox/vda197_user.py', open(USERP, 'rb').read())

    # 阶段1: guest 抓包
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda197_guest.py'], 120000)
    print('[run guest]', c)
    print((r or '')[:5000])

    # 等抓包起来
    print('[wait sniff 10s]')
    time.sleep(10)

    # 阶段2: 用户触发
    uid = uuid.uuid4().hex[:8]
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda197_user.py', uid], 90000)
    print('[user snap]', c)
    print((r or '')[:5000])

    # 阶段3: stopped -> resume -> cat
    print('[wait stop 25s]')
    time.sleep(25)
    st = get_status()
    print('[status]', st)

    if st and st[0] == 'stopped':
        print('[resume]')
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ), timeout=120)
        print('[resume rc]', c, (r or '')[:400])
        time.sleep(15)
        print('[post-resume status]', get_status())
        c, r = cmd(sid, 'sh', ['-c', 'cat /vercel/sandbox/v197s.out 2>&1 | head -300'], 30000)
        print('[v197s.out]', c)
        print((r or '')[:25000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
