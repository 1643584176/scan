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


S = ('echo ===SHARE===; ls -la /run/vercel/share/ 2>&1 | head -20; '
     'echo ===SHARE-W===; echo ctr_test_$$ > /run/vercel/share/_g_test 2>&1 && echo GWRITE_OK; '
     'echo ===SHARE-R===; ls -la /run/vercel/share/_g_test 2>&1; '
     'echo ===VDB-MOUNT===; sudo -n mkdir -p /mnt/vdb2; sudo -n mount /dev/vdb /mnt/vdb2 2>&1; '
     'echo ===VDB-LS===; sudo -n ls /mnt/vdb2/ 2>&1 | head -10; '
     'echo ===VDB-VERCEL===; sudo -n ls -la /mnt/vdb2/vercel/sandbox/ 2>&1 | head -10; '
     'echo ===ROOT-MOUNTINFO===; grep " / " /proc/self/mountinfo; '
     'echo ===SHARE-MOUNTINFO===; grep share /proc/self/mountinfo')
c, r = cmdsh(S, 40000)
print('rc:', c)
print((r or '')[:6000])
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
