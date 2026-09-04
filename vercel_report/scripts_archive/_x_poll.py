# -*- coding: utf-8 -*-
"""拉取 xatk1 沙箱探测结果 + victim hit.log"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

# resume xatk1 (可能已停止)
c, r = api('GET', '/v2/sandboxes/xatk1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
print('resume xatk1:', c, flush=True)
if c == 200:
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid:', sid, flush=True)
    time.sleep(2)
    for fn in ['/vercel/sandbox/xatk.out', '/vercel/sandbox/xatk_guest.py']:
        c, r = cmd(sid, 'sh', ['-c', 'ls -la %s 2>/dev/null; echo ---; cat %s 2>/dev/null | tail -40' % (fn, fn)], timeout_ms=30000)
        print('=== %s -> %d' % (fn, c), flush=True)
        print(r[:3000], flush=True)
        time.sleep(1)

print('=== POLL DONE ===', flush=True)
