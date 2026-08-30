# -*- coding: utf-8 -*-
"""独立根因候选4: v1 API 会话端点差异 — v1 的 cmd/fs/network-policy 是否缺校验或行为不同
(v1 创建无 name 字段, id 即 name; 之前只测过创建+网络可达性)"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

# 1) v1 创建
c, r = api("POST", "/v1/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ})
log('v1 create -> %s | %s' % (c, r[:500]))
if c != 200:
    sys.exit(1)
d = json.loads(r)
log('v1 resp keys: %s' % sorted(d.keys()))
sb = d.get('sandbox', d)
log('sb keys: %s' % sorted(sb.keys()))
log('sb: %s' % json.dumps(sb)[:400])
sb_id = sb.get('id') or sb.get('name')
sid = sb.get('currentSessionId')
log('sb_id=%s sid=%s' % (sb_id, sid))
time.sleep(3)

# 2) v1 cmd 路由探测
log('')
log('===== v1 cmd routes =====')
for path in [
    "/v1/sandboxes/sessions/%s/cmd" % sid,
    "/v1/sandboxes/%s/cmd" % sb_id,
    "/v1/sandboxes/sessions/%s/cmd" % sb_id,
    "/v1/sandboxes/%s/sessions/%s/cmd" % (sb_id, sid),
]:
    c2, r2 = api("POST", path + "?teamId=%s" % TEAM, {"command": "id", "args": [], "wait": True, "timeout": 10000}, 25)
    log('%s -> %s | %s' % (path.replace(sid, 'SID').replace(sb_id, 'ID'), c2, r2[:150].replace(chr(10), ' ')))

# 3) v1 fs/read
log('')
log('===== v1 fs routes =====')
for path in [
    "/v1/sandboxes/sessions/%s/fs/read" % sid,
    "/v1/sandboxes/%s/fs/read" % sb_id,
]:
    c2, r2 = api("POST", path + "?teamId=%s" % TEAM, {"path": "/etc/passwd"}, 25)
    log('%s -> %s | %s' % (path.replace(sid, 'SID').replace(sb_id, 'ID'), c2, r2[:120].replace(chr(10), ' ')))

# 4) v1 network-policy
log('')
log('===== v1 network-policy routes =====')
for path in [
    "/v1/sandboxes/sessions/%s/network-policy" % sid,
    "/v1/sandboxes/%s/network-policy" % sb_id,
]:
    c2, r2 = api("POST", path + "?teamId=%s" % TEAM, {"mode": "deny-all"}, 25)
    log('%s -> %s | %s' % (path.replace(sid, 'SID').replace(sb_id, 'ID'), c2, r2[:120].replace(chr(10), ' ')))

# 5) 清理 (v2 DELETE by name)
if sb_id:
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (sb_id, TEAM, PROJ))
log('DONE')
