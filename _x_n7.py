# -*- coding: utf-8 -*-
"""候选5: interactivePort=26661 attach 通道 — 控制面 attach/interactive/terminal/ssh/ws 路由探测"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n7"})
if c != 200:
    log('create fail %s' % r[:200]); sys.exit(1)
d = json.loads(r)['sandbox']
name, sid = d['name'], d['currentSessionId']
log('n7 name=%s sid=%s interactivePort=%s' % (name, sid, d.get('interactivePort')))
time.sleep(3)

routes = []
for base in ['/v2/sandboxes/sessions/%s' % sid, '/v2/sandboxes/%s' % name, '/v1/sandboxes/%s' % sid]:
    for ep in ['attach', 'interactive', 'terminal', 'ssh', 'ws', 'websocket', 'exec', 'pty', 'connect', 'shell', 'session']:
        routes.append(base + '/' + ep)

log('===== route probe (POST {}) =====')
for p in routes:
    c2, r2 = api("POST", p + "?teamId=%s" % TEAM, {}, 20)
    if c2 not in (404,):
        log('[POST] %-70s -> %s | %s' % (p.replace(sid, 'SID').replace(name, 'NAME'), c2, (r2[:120] if r2 else '').replace(chr(10), ' ')))

log('')
log('===== route probe (GET) =====')
for p in routes:
    c2, r2 = api("GET", p + "?teamId=%s" % TEAM, None, 20)
    if c2 not in (404,):
        log('[GET ] %-70s -> %s | %s' % (p.replace(sid, 'SID').replace(name, 'NAME'), c2, (r2[:120] if r2 else '').replace(chr(10), ' ')))

api("DELETE", "/v2/sandboxes/n7?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
