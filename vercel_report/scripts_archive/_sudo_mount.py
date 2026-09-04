# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

sid = 'sbx_KFdW0QjrpKiuzBC2lPCJsk1okbd8'
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {"command": "sh", "args": ["-c", "sudo -n id 2>&1; sudo -n mount /dev/vda /mnt/vdax 2>&1; ls /mnt/vdax/ 2>&1 | head -20"], "wait": True, "logs": True, "timeout": 30000}, timeout=60)
print('status:', c)
print(r[:3000])
