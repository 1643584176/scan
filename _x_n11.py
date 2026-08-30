# -*- coding: utf-8 -*-
"""候选7: /v2/sandboxes/sessions 列表+详情 — session 对象完整字段/authz"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n11?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n11"})
if c != 200:
    log('create fail %s' % r[:200]); sys.exit(1)
d = json.loads(r)['sandbox']
name, sid = d['name'], d['currentSessionId']
log('n11 sid=%s' % sid)
time.sleep(3)

log('')
log('===== 1) session 详情完整对象 =====')
c, r = api("GET", "/v2/sandboxes/sessions/%s?teamId=%s" % (sid, TEAM))
log('http=%s' % c)
if c == 200:
    log(json.dumps(json.loads(r), indent=1)[:1500])

log('')
log('===== 2) session 列表 =====')
for q in ["?teamId=%s&project=%s" % (TEAM, PROJ), "?project=%s" % PROJ, "?teamId=%s&projectId=%s" % (TEAM, PROJ)]:
    c, r = api("GET", "/v2/sandboxes/sessions%s" % q, None, 20)
    log('GET sessions %-40s -> %s | %s' % (q, c, (r[:300] if r else '').replace(chr(10), ' ')))

log('')
log('===== 3) authz 变体 =====')
c, r = api("GET", "/v2/sandboxes/sessions/%s?teamId=team_BAD" % sid, None, 20)
log('bad team -> %s | %s' % (c, (r[:100] if r else '')))
c, r = api("GET", "/v2/sandboxes/sessions/%s" % sid, None, 20)
log('no team -> %s | %s' % (c, (r[:100] if r else '')))
c, r = api("GET", "/v2/sandboxes/sessions/%s?teamId=%s&projectId=%s" % (sid, TEAM, PROJ), None, 20)
log('with projectId -> %s | %s' % (c, (r[:100] if r else '')))

api("DELETE", "/v2/sandboxes/n11?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
