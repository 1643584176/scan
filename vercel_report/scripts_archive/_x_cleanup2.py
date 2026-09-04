# -*- coding: utf-8 -*-
"""清理: v1/v2 残留 running 沙箱 + 快照配额"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s):
    print(s, flush=True)

# 1) 列出所有沙箱 (v1), 删除 running 的
c, r = api("GET", "/v1/sandboxes?teamId=%s&project=%s&limit=100" % (TEAM, PROJ))
if c == 200:
    lst = json.loads(r).get('sandboxes', [])
    running = [s for s in lst if s.get('status') == 'running']
    log('total sandboxes: %d, running: %d' % (len(lst), len(running)))
    for sb in running:
        sid = sb.get('id')
        c2, r2 = api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (sid, TEAM, PROJ))
        log('DEL %s -> %s | %s' % (sid, c2, r2[:100].replace('\n', ' ')))
        time.sleep(1)
else:
    log('list failed: %s' % r[:200])

# 2) 快照清理
c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=100" % (TEAM, PROJ))
if c == 200:
    snaps = json.loads(r).get('snapshots', [])
    log('snapshots: %d' % len(snaps))
    for s in snaps:
        c2, r2 = api("DELETE", "/v2/sandboxes/snapshots/%s?teamId=%s" % (s.get('id'), TEAM))
        if c2 == 200:
            log('  del snap ok %s' % s.get('id')[-12:])
        else:
            log('  del snap %s -> %s' % (c2, r2[:80].replace('\n', ' ')))
        time.sleep(0.5)
log('DONE')
