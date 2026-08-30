# -*- coding: utf-8 -*-
"""确认 resume 沙箱内无 victim marker (v3: 写文件+轮询)"""
import sys, json, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM

sid = 'sbx_KxhCZ5uQh5F7IpF7wN5Wu1W1jUQg'

# 1) 命令写到输出文件
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {'command': 'sh',
            'args': ['-c', 'ls -la /vercel/sandbox/ > /tmp/o.txt 2>&1; echo === >> /tmp/o.txt; cat /vercel/sandbox/tenant_marker.txt >> /tmp/o.txt 2>&1; echo RC=$? >> /tmp/o.txt'],
            'wait': False, 'timeout': 20000})
print('launch:', c, r[:150], flush=True)
time.sleep(6)

# 2) 读回
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
           {'command': 'cat', 'args': ['/tmp/o.txt'], 'wait': True, 'timeout': 20000})
print('readback status:', c)
print(r, flush=True)
