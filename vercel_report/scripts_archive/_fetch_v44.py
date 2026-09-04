# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ
sid = 'sbx_wyTUjirpR5ajzwOySMP3Ioy8Jekc'
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {"command": "cat", "args": ["/vercel/sandbox/v44d.out"], "wait": True, "logs": True, "timeout": 20000}, timeout=50)
print('status:', c)
print(r[:8000])
