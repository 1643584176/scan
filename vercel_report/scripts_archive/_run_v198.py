# -*- coding: utf-8 -*-
"""v198 驱动: 并发版 - guest 抓包(210s) 同时 用户触发 CreateSnapshot
抓包结果通过 guest cmd 流式输出获取 (COW 循环)
时序: guest 启动 -> 8s 后用户触发 u1/u2 -> 等抓包结束"""
import sys, os, time, base64, json, uuid, threading
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v198'
GUEST = r'D:\scan\skills\non-traditional-vuln-hunting\vda198_guest.py'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda198_probe_guest.py'
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

    inject(sid, '/vercel/sandbox/vda198_guest.py', open(GUEST, 'rb').read())
    inject(sid, '/vercel/sandbox/vda198_probe_guest.py', open(PAY, 'rb').read())
    inject(sid, '/vercel/sandbox/vda197_user.py', open(USERP, 'rb').read())

    res = {}

    def run_guest():
        c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda198_guest.py'], 240000)
        res['guest'] = (c, r)

    # 阶段1: guest 抓包线程
    th = threading.Thread(target=run_guest, daemon=True)
    th.start()
    print('[guest started]')

    # 阶段2: 8s 后用户触发
    time.sleep(8)
    uid = uuid.uuid4().hex[:8]
    print('[trigger user %s]' % uid)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda197_user.py', uid], 90000)
    print('[user snap]', c)
    print((r or '')[:5000])

    # 阶段3: 等待
    time.sleep(25)
    print('[status]', get_status())

    # 等 guest 抓包完成
    th.join(timeout=260)
    gc, gr = res.get('guest', (None, None))
    print('[guest rc]', gc)
    print((gr or '')[:40000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
