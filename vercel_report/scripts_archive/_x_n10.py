# -*- coding: utf-8 -*-
"""候选6: 控制面端点系统枚举 — 未测端点 (exec/logs/files/commands/stop/share/access/events/status)"""
import json, sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n10?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n10"})
if c != 200:
    log('create fail %s' % r[:200]); sys.exit(1)
d = json.loads(r)['sandbox']
name, sid = d['name'], d['currentSessionId']
log('n10 sid=%s' % sid)
time.sleep(3)

paths = [
    # (method, path, body)
    ("POST", "/v2/sandboxes/sessions/%s/exec" % sid, {"command": "id"}),
    ("POST", "/v2/sandboxes/sessions/%s/logs" % sid, {}),
    ("GET",  "/v2/sandboxes/sessions/%s/logs" % sid, None),
    ("GET",  "/v2/sandboxes/sessions/%s/files" % sid, None),
    ("GET",  "/v2/sandboxes/sessions/%s/status" % sid, None),
    ("POST", "/v2/sandboxes/sessions/%s/events" % sid, {}),
    ("GET",  "/v2/sandboxes/sessions/%s/commands" % sid, None),
    ("GET",  "/v2/sandboxes/%s/commands" % name, None),
    ("POST", "/v2/sandboxes/%s/stop" % name, {}),
    ("POST", "/v2/sandboxes/%s/resume" % name, {}),
    ("GET",  "/v2/sandboxes/%s/share" % name, None),
    ("POST", "/v2/sandboxes/%s/share" % name, {}),
    ("GET",  "/v2/sandboxes/%s/access" % name, None),
    ("POST", "/v2/sandboxes/%s/access" % name, {}),
    ("GET",  "/v2/sandboxes/%s/invites" % name, None),
    ("POST", "/v2/sandboxes/sessions/%s/snapshots" % sid, {}),
    ("GET",  "/v2/sandboxes/sessions/%s" % sid, None),
    ("GET",  "/v2/sandboxes/sessions", None),
    ("POST", "/v2/sandboxes/sessions/%s/terminal" % sid, {}),
    ("GET",  "/v2/sandboxes/sessions/%s/interactive" % sid, None),
]

log('===== endpoint sweep =====')
for m, p, b in paths:
    c2, r2 = api(m, p + "?teamId=%s" % TEAM, b, 20)
    disp = p.replace(sid, 'SID').replace(name, 'NAME')
    if c2 != 404:
        log('[%s] %-64s -> %s | %s' % (m, disp, c2, (r2[:160] if r2 else '').replace(chr(10), ' ')))
    else:
        log('[%s] %-64s -> 404' % (m, disp))

api("DELETE", "/v2/sandboxes/n10?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
