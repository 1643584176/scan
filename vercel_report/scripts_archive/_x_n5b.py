# -*- coding: utf-8 -*-
"""独立根因候选4b: v1 会话端点 (v1 无 currentSessionId, 尝试 id 直接作为会话标识)"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

c, r = api("POST", "/v1/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ})
log('v1 create -> %s' % c)
if c != 200:
    sys.exit(1)
sb = json.loads(r)['sandbox']
sb_id = sb['id']
log('sb_id=%s' % sb_id)
time.sleep(3)

# GET 查询是否返回 currentSessionId
c, r = api("GET", "/v1/sandboxes/%s?teamId=%s" % (sb_id, TEAM))
log('v1 GET -> %s | %s' % (c, r[:300]))

log('')
log('===== v1 cmd routes =====')
for path in [
    "/v1/sandboxes/%s/cmd" % sb_id,
    "/v1/sandboxes/sessions/%s/cmd" % sb_id,
]:
    c2, r2 = api("POST", path + "?teamId=%s" % TEAM, {"command": "id", "args": [], "wait": True, "timeout": 10000}, 25)
    log('%s -> %s | %s' % (path.replace(sb_id, 'ID'), c2, (r2[:160] if r2 else '').replace(chr(10), ' ')))

log('')
log('===== v1 fs/read =====')
for path in [
    "/v1/sandboxes/%s/fs/read" % sb_id,
    "/v1/sandboxes/sessions/%s/fs/read" % sb_id,
]:
    c2, r2 = api("POST", path + "?teamId=%s" % TEAM, {"path": "/etc/passwd"}, 25)
    log('%s -> %s | %s' % (path.replace(sb_id, 'ID'), c2, (r2[:120] if r2 else '').replace(chr(10), ' ')))

log('')
log('===== v1 network-policy =====')
for path in [
    "/v1/sandboxes/%s/network-policy" % sb_id,
    "/v1/sandboxes/sessions/%s/network-policy" % sb_id,
]:
    c2, r2 = api("POST", path + "?teamId=%s" % TEAM, {"mode": "deny-all"}, 25)
    log('%s -> %s | %s' % (path.replace(sb_id, 'ID'), c2, (r2[:120] if r2 else '').replace(chr(10), ' ')))

# v1 DELETE
c, r = api("DELETE", "/v1/sandboxes/%s?teamId=%s" % (sb_id, TEAM))
log('v1 DELETE -> %s | %s' % (c, (r[:120] if r else '')))
# v2 DELETE fallback
api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (sb_id, TEAM, PROJ))
log('DONE')
