# -*- coding: utf-8 -*-
"""确认路径2 resume 恢复的沙箱内无 victim marker"""
import sys
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM

sid = 'sbx_KxhCZ5uQh5F7IpF7wN5Wu1W1jUQg'
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {'command': 'sh', 'args': ['-c', 'ls /vercel/sandbox/ ; cat /vercel/sandbox/tenant_marker.txt 2>&1; echo RC=$?'],
            'wait': True, 'timeout': 30000})
print('status:', c)
print(r[-900:])
