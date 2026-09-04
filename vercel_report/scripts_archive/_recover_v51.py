# -*- coding: utf-8 -*-
import sys, json, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

# 找 v51 快照
c, r = api('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=50' % (TEAM, PROJ), timeout=30)
d = json.loads(r)
snap = None
for s in d.get('snapshots', []):
    if s.get('sourceSessionId') == 'sbx_nGFpJbzTbcCxxpLrAGsLmTaKdndt':
        snap = s['id']
        print('v51 snap:', snap, s['status'])
        break
if not snap:
    # 最新的 created 快照
    for s in d.get('snapshots', []):
        if s['status'] == 'created':
            print('candidate:', s['id'], s.get('sourceSessionId'))
    sys.exit(1)

api('DELETE', '/v2/sandboxes/v51r?teamId=%s&projectId=%s' % (TEAM, PROJ))
time.sleep(1)
body = {"projectId": PROJ, "name": "v51r",
        "source": {"type": "snapshot", "snapshotId": snap}}
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, body, timeout=120)
print('create v51r:', c, r[:300])
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('sid:', sid)
time.sleep(3)
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {"command": "sh", "args": ["-c", "sudo -n mount /dev/vda /mnt/vdax 2>&1; ls /mnt/vdax/root/ 2>&1; echo ===C===; cat /mnt/vdax/root/v51c.out 2>&1; echo ===M===; cat /mnt/vdax/root/v51m.out 2>&1"], "wait": True, "logs": True, "timeout": 40000}, timeout=80)
print('cmd:', c)
print(r[:12000])
