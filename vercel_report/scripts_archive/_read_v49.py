# -*- coding: utf-8 -*-
import sys, json, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/v49?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ), timeout=120)
print('resume v49:', c, r[:400])
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('sid:', sid)
time.sleep(2)
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {"command": "sh", "args": ["-c", "ls -la /vercel/sandbox/ 2>&1; echo ===; cat /vercel/sandbox/v49.out 2>&1"], "wait": True, "logs": True, "timeout": 30000}, timeout=60)
print('cmd:', c)
print(r[:8000])
