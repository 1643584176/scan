# -*- coding: utf-8 -*-
"""drive 面探测: victim 账号创建 drive + 挂载写 marker, 供跨租户 drive 测试
用法: python victim_drive_setup.py <drive_name>
输出: DRIVE_NAME / MARKER
"""
import json, sys, time, uuid
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver2 import api, TEAM2, PROJ2

dname = sys.argv[1]
marker = 'VICTIM_DRIVE_MARKER_%s' % uuid.uuid4().hex[:12]

# 1) 创建/获取 drive
c, r = api('POST', '/v2/sandboxes/drives?teamId=%s&projectId=%s' % (TEAM2, PROJ2),
           {'name': dname})
print('get-or-create drive:', c, r[:400], flush=True)
if c not in (200, 201):
    print('DRIVE NOT AVAILABLE:', c, flush=True)
    sys.exit(1)

# 2) 创建 victim3 沙箱并挂载 drive
sname = 'victim3'
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (sname, TEAM2, PROJ2))
time.sleep(2)
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM2,
           {'projectId': PROJ2, 'name': sname,
            'mounts': {'/mnt/drive': {'drive': dname, 'mode': 'read-write'}}})
print('create sandbox with mount:', c, r[:300], flush=True)
if c != 200:
    print('MOUNT FAILED', flush=True)
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('VICTIM_SID:', sid, flush=True)
time.sleep(3)

# 3) 写 marker 到 drive
c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM2),
           {'command': 'sh',
            'args': ['-c', 'echo %s > /mnt/drive/drive_marker.txt; cat /mnt/drive/drive_marker.txt; ls -la /mnt/drive/' % marker],
            'wait': True, 'logs': True, 'timeout': 30000})
print('drive write:', c, r[-400:], flush=True)

print('DRIVE_NAME:', dname, flush=True)
print('MARKER:', marker, flush=True)
print('=== VICTIM DRIVE READY ===', flush=True)
