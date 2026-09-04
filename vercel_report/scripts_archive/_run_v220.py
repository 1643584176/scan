# -*- coding: utf-8 -*-
"""v220 驱动: interactive 触发 26661 -> guest 协议指纹枚举 (banner/HTTP/ConnectRPC/ws/CONNECT)"""
import sys, os, time, base64, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v220'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda220_probe_guest.py'


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

    inject(sid, '/vercel/sandbox/vda220_probe_guest.py', open(PAY, 'rb').read())

    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {'command': 'python3', 'args': ['/vercel/sandbox/vda220_probe_guest.py'],
                'wait': False, 'timeout': 200000}, timeout=30)
    print('[payload bg]', c, (r or '')[:200])
    time.sleep(6)

    # 调用 interactive, 并把真实 token 写入沙箱供 ws 探测
    c, r = api('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {}, timeout=60)
    print('[interactive]', c, (r or '')[:300])
    tok = ''
    try:
        d = json.loads(r)
        tok = d.get('token') or ''
        print('url=%s' % d.get('url'))
    except Exception:
        pass
    if tok:
        c, r = cmd(sid, 'python3', ['-c', 'open("/vercel/sandbox/v220_tok","w").write("%s")' % tok], 20000)
        print('[tok write]', c)

    time.sleep(150)
    c, r = cmd(sid, 'bash', ['-c', 'cat /vercel/sandbox/v220c.out 2>&1'], 30000)
    print('[read v220c.out]', c)
    print((r or '')[:30000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
