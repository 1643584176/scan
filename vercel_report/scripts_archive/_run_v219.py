# -*- coding: utf-8 -*-
"""v219 驱动: interactive API 触发 -> 观察 26661 条件监听 (guest tcp6 时序)
流程: 建沙箱 -> 注入 payload 后台跑 -> 驱动 POST interactive -> 写 v219_go 标记 ->
等待观察结束 -> 读 v219c.out"""
import sys, os, time, base64, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v219'
PAY = r'D:\scan\skills\non-traditional-vuln-hunting\vda219_probe_guest.py'


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

    inject(sid, '/vercel/sandbox/vda219_probe_guest.py', open(PAY, 'rb').read())

    # 后台跑 payload (不 wait, 让 watcher 持续观察)
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {'command': 'python3', 'args': ['/vercel/sandbox/vda219_probe_guest.py'],
                'wait': False, 'timeout': 150000}, timeout=30)
    print('[payload bg]', c, (r or '')[:200])
    time.sleep(6)

    # 调用 interactive API (触发条件)
    print('[interactive call...]')
    c, r = api('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {}, timeout=60)
    print('[interactive]', c, (r or '')[:400])
    try:
        d = json.loads(r)
        print('url=%s token=%s' % (d.get('url'), (d.get('token') or '')[:20] + '...' if d.get('token') else None))
    except Exception:
        pass

    # 写触发标记 (payload 看到后继续观察 60s)
    c, r = cmd(sid, 'bash', ['-c', 'touch /vercel/sandbox/v219_go'], 20000)
    print('[mark]', c)

    # 等 payload 完成
    time.sleep(75)
    c, r = cmd(sid, 'bash', ['-c', 'cat /vercel/sandbox/v219c.out 2>&1'], 30000)
    print('[read v219c.out]', c)
    print((r or '')[:30000])

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED total %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
