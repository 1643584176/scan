# -*- coding: utf-8 -*-
"""v64q 定位 cell/sandboxctrl 二进制 + metadata db"""
import sys, os, time, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

NAME = 'v64q'
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
         'echo ===OPT===; ls -la /mnt/vdax/opt/ 2>&1 | head -30; '
         'echo ===LOCAL===; ls -la /mnt/vdax/usr/local/bin/ 2>&1 | head -30; '
         'echo ===VERCEL===; ls -la /mnt/vdax/vercel/ 2>&1 | head -30; '
         'echo ===SNAP2V===; ls -la /mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/2/fs/vercel/ 2>&1 | head -20; '
         'echo ===SNAP6V===; ls -la /mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/6/fs/vercel/ 2>&1 | head -20; '
         'echo ===SNAP5BIN===; ls -la /mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/5/fs/bin/ 2>&1 | head -30; '
         'echo ===SNAP5U===; ls -la /mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/5/fs/usr/ 2>&1 | head -20; '
         'echo ===META===; ls -la /mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/ 2>&1; '
         'echo ===TASKDIR===; ls -la /mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default/ 2>&1 | head -20')
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c", s], "wait": True, "logs": True, "timeout": 60000},
               timeout=100)
    print('[cmd]', c)
    print((r or '')[:12000])
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED')


if __name__ == '__main__':
    main()
