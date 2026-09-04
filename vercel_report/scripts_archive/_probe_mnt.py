# -*- coding: utf-8 -*-
import sys, json, time
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


S = ('echo ===MOUNTS===; cat /proc/mounts | grep -vE "proc|sysfs|devpts|cgroup|mqueue|shm" ; '
     'echo ===SANDBOX-MNT===; cat /proc/mounts | grep -iE "sandbox|overlay|vercel"; '
     'echo ===DEV===; ls -la /dev/ | grep -E "vd|sd|xvd|nvme"; '
     'echo ===FINDMNT===; findmnt /vercel/sandbox 2>&1; '
     'echo ===STAT===; stat -f /vercel/sandbox 2>&1 | head -8; '
     'echo ===MOUNT-INFO===; cat /proc/self/mountinfo | grep sandbox | head -5')
c, r = cmdsh(S, 40000)
print('rc:', c)
print((r or '')[:8000])
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
