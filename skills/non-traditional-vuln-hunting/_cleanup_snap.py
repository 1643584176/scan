# -*- coding: utf-8 -*-
"""清理: attacker 沙箱 (atk_snapx/y) + victim2 + victim2 快照"""
import sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ
from vercel_driver2 import api as api2, TEAM2, PROJ2

# attacker 侧清理
for name in ('atk_snapx', 'atk_snapy'):
    c, r = api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    print('del %s:' % name, c, flush=True)
    time.sleep(1)

# attacker 侧快照 (atk_snapy 自动快照)
for snap in ('snap_VzIQA77UApANP7IsDEUQxGVX8Vb9',):
    c, r = api('DELETE', '/v2/sandboxes/snapshots/%s?teamId=%s' % (snap, TEAM))
    print('del attacker snap %s:' % snap, c, flush=True)
    time.sleep(1)

# victim 侧清理
c, r = api2('DELETE', '/v2/sandboxes/victim2?teamId=%s&projectId=%s' % (TEAM2, PROJ2))
print('del victim2:', c, flush=True)
time.sleep(1)
c, r = api2('DELETE', '/v2/sandboxes/snapshots/snap_sBuZeYV3skMFham5CRG3f1JOmbzo?teamId=%s' % TEAM2)
print('del victim snap:', c, flush=True)

print('=== CLEANUP DONE ===', flush=True)
