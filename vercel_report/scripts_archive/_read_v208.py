# -*- coding: utf-8 -*-
"""抢救 v208 沙箱: 读 hook log + 检查重放写文件效果"""
import sys
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, cmd

sid = 'sbx_5Cco0Ofkw5qA31yxK3HfjsuLEZCp'

c, r = cmd(sid, 'cat', ['/vercel/sandbox/v208hook.log'], 20000)
print('[hook log]', c)
print((r or '')[:25000])

c, r = cmd(sid, 'bash', ['-c', 'ls -la /tmp/v208_a /tmp/v208_id 2>&1; echo ---; cat /tmp/v208_a /tmp/v208_id 2>&1'], 15000)
print('[replay effect]', c)
print((r or '')[:2000])
