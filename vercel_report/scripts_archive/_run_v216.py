# -*- coding: utf-8 -*-
"""v216 驱动: driveId 变体触发快照判定 + resume 读落盘文件"""
import sys, os, time, base64, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v216'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda216_probe_user.py'


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

    inject(sid, '/vercel/sandbox/vda216_probe_user.py', open(PAY, 'rb').read())

    c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda216_probe_user.py', sid], 60000)
    print('[run payload]', c)
    print((r or '')[:8000])

    time.sleep(2)
    st, snap, sess = get_status()
    print('[status] %s snap=%s' % (st, snap))

    # 若 stopped -> resume 读落盘文件
    if st == 'stopped':
        print('[try resume...]')
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (NAME, TEAM, PROJ))
        print('[resume]', c, (r or '')[:300])
        time.sleep(6)
        st2, snap2, sess2 = get_status()
        print('[status2] %s session=%s' % (st2, sess2))
        if st2 == 'running' and sess2:
            c, r = cmd(sess2, 'bash', ['-c', 'ls -la /vercel/sandbox/v216_* 2>&1; echo ---; for f in /vercel/sandbox/v216_*; do echo \"== $f ==\"; cat \"$f\"; echo; done'], 20000)
            print('[read files]', c)
            print((r or '')[:8000])
        else:
            print('[resume failed] trying old session')
            c, r = cmd(sess, 'bash', ['-c', 'ls -la /vercel/sandbox/v216_* 2>&1; for f in /vercel/sandbox/v216_*; do echo \"== $f ==\"; cat \"$f\"; echo; done'], 20000)
            print('[read files old]', c)
            print((r or '')[:8000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
