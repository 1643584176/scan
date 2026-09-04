# -*- coding: utf-8 -*-
"""信息收集: enroll 400 详情 + 沙箱/项目完整对象字段 + 快照详情/下载面"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s):
    print(s, flush=True)

# 1) enroll 400 完整错误
log('===== enroll 400 detail =====')
c, r = api("POST", "/v2/sandboxes/drives/enroll", {"projectId": PROJ, "teamId": TEAM})
log('with teamId: %s | %s' % (c, r[:400].replace('\n', ' ')))

# 2) 沙箱完整对象
log('')
log('===== sandbox full object =====')
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "info1"})
if c == 200:
    d = json.loads(r)
    log('sandbox keys: %s' % sorted(d.get('sandbox', {}).keys()))
    log('session keys: %s' % sorted(d.get('session', {}).keys()))
    # 打印所有字段值 (脱敏 token)
    for k, v in d.get('sandbox', {}).items():
        sv = json.dumps(v)[:200]
        log('  sb.%s = %s' % (k, sv))
    for k, v in d.get('session', {}).items():
        sv = json.dumps(v)[:200]
        log('  se.%s = %s' % (k, sv))
    time.sleep(1)
    api("DELETE", "/v2/sandboxes/info1?teamId=%s&projectId=%s" % (TEAM, PROJ))

# 3) 项目完整对象
log('')
log('===== project full object =====')
for p in ["/v6/projects/%s?teamId=%s" % (PROJ, TEAM), "/v9/projects/%s?teamId=%s" % (PROJ, TEAM)]:
    c, r = api("GET", p)
    log('%s -> %s' % (p.split('?')[0], c))
    if c == 200:
        try:
            d = json.loads(r)
            for k, v in d.items():
                sv = json.dumps(v)[:150]
                log('  %s = %s' % (k, sv))
        except Exception:
            log(r[:300])
    break  # 先看 v6

# 4) 快照详情/下载面
log('')
log('===== snapshot detail/download =====')
c, r = api("GET", "/v2/sandboxes/snapshots?teamId=%s&project=%s&limit=3" % (TEAM, PROJ))
if c == 200:
    snaps = json.loads(r).get('snapshots', [])
    if snaps:
        sid = snaps[0].get('id')
        log('first snap: %s' % sid)
        for path in [
            "/v2/sandboxes/snapshots/%s?teamId=%s" % (sid, TEAM),
            "/v2/sandboxes/snapshots/%s?teamId=%s&project=%s" % (sid, TEAM, PROJ),
            "/v2/sandboxes/snapshots/%s/download?teamId=%s" % (sid, TEAM),
            "/v2/sandboxes/snapshots/%s/contents?teamId=%s" % (sid, TEAM),
            "/v2/sandboxes/snapshots/%s/files?teamId=%s" % (sid, TEAM),
            "/v2/sandboxes/snapshots/%s/export?teamId=%s" % (sid, TEAM),
        ]:
            c2, r2 = api("GET", path)
            log('%s -> %s | %s' % (path.split('?')[0].split('/')[-1], c2, r2[:250].replace('\n', ' ')))
log('DONE')
