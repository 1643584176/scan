# -*- coding: utf-8 -*-
"""候选9: drives 数据面 — 创建/列表/挂载机制 + fork + 快照详情 + image 字段"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

Q = "?teamId=%s&projectId=%s" % (TEAM, PROJ)

# 0) drives
log('===== 0) drives =====')
c, r = api("GET", "/v2/sandboxes/drives" + Q, None, 20)
log('GET drives -> %s | %s' % (c, (r[:300] if r else '').replace(chr(10), ' ')))
c, r = api("POST", "/v2/sandboxes/drives/d1" + Q, {}, 25)
log('POST drives/d1 -> %s | %s' % (c, (r[:400] if r else '').replace(chr(10), ' ')))
c, r = api("GET", "/v2/sandboxes/drives/d1" + Q, None, 20)
log('GET drives/d1 -> %s | %s' % (c, (r[:300] if r else '').replace(chr(10), ' ')))

# 1) 建沙箱 + 挂载尝试
api("DELETE", "/v2/sandboxes/n13?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
for tag, body in [
    ('no-drive', {"projectId": PROJ, "name": "n13"}),
]:
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, body, 25)
    log('v4 create [%s] -> %s | %s' % (tag, c, (r[:200] if r else '').replace(chr(10), ' ')))
    if c == 200:
        break
d = json.loads(r)['sandbox']
name, sid = d['name'], d['currentSessionId']
log('n13 sid=%s' % sid)
time.sleep(3)

# 2) fork 尝试 (body/query 变体)
log('')
log('===== 1) fork =====')
for tag, q, b in [
    ('query-projectId', Q, {}),
    ('body-projectId', "?teamId=%s" % TEAM, {"projectId": PROJ}),
    ('empty', '', {}),
]:
    c, r = api("POST", "/v2/sandboxes/%s/fork%s" % (name, q), b, 25)
    log('[%s] -> %s | %s' % (tag, c, (r[:220] if r else '').replace(chr(10), ' ')))
    if c == 200:
        try:
            d2 = json.loads(r)
            sb = d2.get('sandbox', {})
            log('  fork keys: %s' % sorted(sb.keys()))
            fname = sb.get('name')
            log('  fork name: %s' % fname)
            if fname:
                api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (fname, TEAM, PROJ))
        except Exception as e:
            log('  parse: %s' % e)

# 3) 快照详情
log('')
log('===== 2) snapshot detail =====')
c, r = api("GET", "/v2/sandboxes/snapshots?project=%s" % PROJ, None, 20)
log('snap list -> %s' % c)
snap_id = None
if c == 200:
    try:
        snaps = json.loads(r).get('snapshots', [])
        log('snap count: %d' % len(snaps))
        for s in snaps[:5]:
            log('  snap: %s | %s' % (s.get('id'), json.dumps(s)[:220]))
        snap_id = snaps[0].get('id') if snaps else None
    except Exception as e:
        log('  parse: %s' % e)
if snap_id:
    c, r = api("GET", "/v2/sandboxes/snapshots/%s?project=%s" % (snap_id, PROJ), None, 20)
    log('GET snap/%s -> %s | %s' % (snap_id[-8:], c, (r[:400] if r else '').replace(chr(10), ' ')))

# 4) image 字段 (v3/v4 创建)
log('')
log('===== 3) image 字段 =====')
for v in ['v3', 'v4']:
    c, r = api("POST", "/%s/sandboxes?teamId=%s" % (v, TEAM),
               {"projectId": PROJ, "name": "n13_%s" % v, "image": "docker.io/library/alpine:latest"}, 25)
    log('%s image=alpine -> %s | %s' % (v, c, (r[:220] if r else '').replace(chr(10), ' ')))
    if c == 200:
        try:
            sb = json.loads(r)['sandbox']
            log('  runtime=%s image=%s' % (sb.get('runtime'), sb.get('image')))
        except Exception:
            pass
        api("DELETE", "/v2/sandboxes/n13_%s?teamId=%s&projectId=%s" % (v, TEAM, PROJ))

# 5) 清理 (沙箱+快照+drive)
api("DELETE", "/v2/sandboxes/n13?teamId=%s&projectId=%s" % (TEAM, PROJ))
api("DELETE", "/v2/sandboxes/drives/d1" + Q)
if snap_id:
    api("DELETE", "/v2/sandboxes/snapshots/%s?project=%s" % (snap_id, PROJ))
log('DONE')
