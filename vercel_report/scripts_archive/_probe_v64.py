# -*- coding: utf-8 -*-
"""v64p 结构探测: containerd 目录 + snapshotter rootfs 结构"""
import sys, os, time, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

NAME = 'v64p'
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
         'echo ===ROOT===; ls /mnt/vdax/ 2>&1; '
         'echo ===CONTD===; ls /mnt/vdax/var/lib/containerd/ 2>&1; '
         'echo ===CONTD_RUN===; ls /mnt/vdax/run/containerd/ 2>&1; '
         'echo ===SNAPS===; ls /mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/ 2>&1 | head -40; '
         'echo ===FS_TOPS===; for d in /mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/*/fs; '
         'do echo --$d; ls "$d" 2>/dev/null | head -12; done 2>&1 | head -120; '
         'echo ===CTR_BIN===; ls -la /mnt/vdax/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256/ 2>&1 | head -10')
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c", s], "wait": True, "logs": True, "timeout": 60000},
               timeout=100)
    print('[cmd]', c)
    print((r or '')[:12000])
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    print('CLEANED')


if __name__ == '__main__':
    main()
