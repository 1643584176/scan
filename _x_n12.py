# -*- coding: utf-8 -*-
"""候选8: 官方文档端点全家桶 — drives/fork/snapshot手动/stop/extend-timeout/mkdir/cmd管理/v3/v4"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

# 0) drives 探索
log('===== 0) drives =====')
for m, p, b in [
    ("GET",  "/v2/sandboxes/drives", None),
    ("POST", "/v2/sandboxes/drives/d1", {}),
    ("GET",  "/v2/sandboxes/drives/d1", None),
    ("DELETE","/v2/sandboxes/drives/d1", None),
]:
    c, r = api(m, p + "?teamId=%s" % TEAM, b, 20)
    log('[%s] %-40s -> %s | %s' % (m, p, c, (r[:250] if r else '').replace(chr(10), ' ')))

# 1) 建沙箱
api("DELETE", "/v2/sandboxes/n12?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n12"})
if c != 200:
    log('create fail %s' % r[:200]); sys.exit(1)
d = json.loads(r)['sandbox']
name, sid = d['name'], d['currentSessionId']
log('n12 sid=%s' % sid)
time.sleep(3)

# 2) 手动快照
log('')
log('===== 1) snapshot/fork/stop/extend/mkdir =====')
for m, p, b, tag in [
    ("POST", "/v2/sandboxes/sessions/%s/snapshot" % sid, {}, 'snapshot'),
    ("POST", "/v2/sandboxes/%s/fork" % name, {}, 'fork'),
    ("POST", "/v2/sandboxes/sessions/%s/stop" % sid, {}, 'stop'),
    ("POST", "/v2/sandboxes/sessions/%s/extend-timeout" % sid, {}, 'extend-empty'),
    ("POST", "/v2/sandboxes/sessions/%s/extend-timeout" % sid, {"timeout": 600000}, 'extend-600'),
    ("POST", "/v2/sandboxes/sessions/%s/fs/mkdir" % sid, {"path": "/tmp/n12dir"}, 'mkdir'),
]:
    c, r = api(m, p + "?teamId=%s" % TEAM, b, 25)
    log('[%s] %-16s -> %s | %s' % (tag, m, c, (r[:220] if r else '').replace(chr(10), ' ')))

# 3) cmd 管理 (先跑一个命令拿 cmdId)
log('')
log('===== 2) cmd 管理 =====')
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "sh", "args": ["-c", "sleep 2; echo CMD_DONE_2026"], "wait": False}, 25)
log('cmd start -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))
cmd_id = None
try:
    cmd_id = json.loads(r).get('command', {}).get('id')
except Exception:
    pass
log('cmd_id=%s' % cmd_id)
c, r = api("GET", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM), None, 20)
log('cmd list -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))
if cmd_id:
    time.sleep(3)
    c, r = api("GET", "/v2/sandboxes/sessions/%s/cmd/%s?teamId=%s" % (sid, cmd_id, TEAM), None, 20)
    log('cmd get -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))
    c, r = api("GET", "/v2/sandboxes/sessions/%s/cmd/%s/logs?teamId=%s" % (sid, cmd_id, TEAM), None, 20)
    log('cmd logs -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd/%s/kill?teamId=%s" % (sid, cmd_id, TEAM), {}, 20)
    log('cmd kill -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))

# 4) v3/v4 创建
log('')
log('===== 3) v3/v4 create =====')
for v in ['v3', 'v4']:
    c, r = api("POST", "/%s/sandboxes?teamId=%s" % (v, TEAM), {"projectId": PROJ, "name": "n12_%s" % v}, 25)
    log('%s create -> %s | %s' % (v, c, (r[:250] if r else '').replace(chr(10), ' ')))
    if c == 200:
        try:
            d2 = json.loads(r)
            sb = d2.get('sandbox', {})
            log('%s keys: %s' % (v, sorted(sb.keys())))
            api("DELETE", "/v2/sandboxes/n12_%s?teamId=%s&projectId=%s" % (v, TEAM, PROJ))
        except Exception as e:
            log('%s parse err %s' % (v, e))

# 5) 清理
api("DELETE", "/v2/sandboxes/n12?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
