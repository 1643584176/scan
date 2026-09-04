# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

sid = 'sbx_KFdW0QjrpKiuzBC2lPCJsk1okbd8'
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {"command": "sh", "args": ["-c", "ls -la /vercel/sandbox/ 2>&1; echo ===; cat /vercel/sandbox/v50.out 2>&1"], "wait": True, "logs": True, "timeout": 30000}, timeout=60)
print('status:', c)
print(r[:9000])
