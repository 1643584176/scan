# -*- coding: utf-8 -*-
"""v218 驱动: 26661 条件监听时序观察 (CreateSnapshot 触发前后) + host 集群网段扫描
payload 落盘 /vercel/sandbox/v218c.out; stopped 后 resume 回读"""
import sys, os, time, base64, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v218'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda218_probe_guest.py'


def inject(sid, dst, content):
    b64 = base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode()
    s = "import base64;open('%s','wb').write(base64.b64decode('%s'))" % (dst, b64)
    c, r = cmd(sid, 'python3', ['-c', s], 60000)
    print('[inject %s]' % dst, c)
    return c


def get_status():
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        sb = d.get('sandbox', {})
        return sb.get('status'), sb.get('currentSnapshotId'), sb.get('currentSessionId')
    except Exception:
        return None, None, None


def main():
    t0 = time.time()
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    sid = fresh_sandbox(NAME)
    print('[create ok] %.0fs sid=%s' % (time.time() - t0, sid))

    inject(sid, '/vercel/sandbox/vda218_probe_guest.py', open(PAY, 'rb').read())

    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda218_probe_guest.py'], 60000)
    print('[run payload]', c)
    print((r or '')[:4000])

    time.sleep(3)
    st, snap, sess = get_status()
    print('[status] %s snap=%s sess=%s' % (st, snap, sess))

    # stopped -> resume 读落盘结果
    if st == 'stopped':
        print('[try resume...]')
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ))
        print('[resume]', c, (r or '')[:300])
        time.sleep(6)
        st2, _, sess2 = get_status()
        print('[status2] %s sess=%s' % (st2, sess2))
        if st2 == 'running' and sess2:
            c, r = cmd(sess2, 'bash', ['-c', 'cat /vercel/sandbox/v218c.out 2>&1'], 30000)
            print('[read v218c.out]', c)
            print((r or '')[:20000])
        else:
            print('[resume failed]')
    else:
        # 可能没被 stop, 直接读
        c, r = cmd(sess or sid, 'bash', ['-c', 'cat /vercel/sandbox/v218c.out 2>&1'], 30000)
        print('[read v218c.out]', c)
        print((r or '')[:20000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
