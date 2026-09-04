# -*- coding: utf-8 -*-
"""控制面格式修正: projectId 在 query 的 fork / project 在 query 的 list-snapshots"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

# C5b: list snapshots with project query
c, r = api('GET', '/v2/sandboxes/snapshots?teamId=%s&project=%s' % (TEAM, PROJ))
print('[C5b-list-snapshots] http=%s | %s' % (c, r[:800]), flush=True)

# C6b: fork with projectId query
c, r = api('POST', '/v2/sandboxes/npol1/fork?teamId=%s&projectId=%s' % (TEAM, PROJ), {})
print('[C6b-fork] http=%s | %s' % (c, r[:400]), flush=True)
fork_name = None
try:
    dd = json.loads(r)
    fork_name = dd.get('name') or (dd.get('sandbox') or {}).get('name')
except Exception:
    pass
print('    fork name:', fork_name, flush=True)

if fork_name:
    time.sleep(3)
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (fork_name, TEAM, PROJ))
    print('[C7-fork-readback] http=%s | %s' % (c, r[:600]), flush=True)
    c, r = api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (fork_name, TEAM, PROJ))
    print('[C8-fork-cleanup] http=%s | %s' % (c, r[:200]), flush=True)

print('=== CTRL3 DONE ===', flush=True)
