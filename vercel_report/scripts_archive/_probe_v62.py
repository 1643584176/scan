# -*- coding: utf-8 -*-
"""v62 前置探测: 宿主工具集 (mount/chroot/busybox/python/perl) + 快速跑完"""
import sys, os, time, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

NAME = 'v62p'
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
    s = ('mkdir -p /mnt/vdax; sudo mount /dev/vda /mnt/vdax 2>&1; '
         'echo ===BIN===; ls /mnt/vdax/bin/ 2>&1; '
         'echo ===USRBIN===; ls /mnt/vdax/usr/bin/ 2>&1 | head -80; '
         'echo ===SBIN===; ls /mnt/vdax/sbin/ 2>&1; '
         'echo ===USRSBIN===; ls /mnt/vdax/usr/sbin/ 2>&1 | head -40; '
         'echo ===USRLOCAL===; ls /mnt/vdax/usr/local/bin/ 2>&1 | head -40; '
         'echo ===BUSYBOX===; ls -la /mnt/vdax/bin/busybox /mnt/vdax/usr/bin/busybox 2>&1; '
         'echo ===LIB64===; ls /mnt/vdax/lib64/ 2>&1 | head -20')
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c", s], "wait": True, "logs": True, "timeout": 40000},
               timeout=80)
    print('[cmd]', c)
    print((r or '')[:8000])
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED')


if __name__ == '__main__':
    main()
