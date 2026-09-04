# -*- coding: utf-8 -*-
"""独立根因候选4c: v1 cmd schema 差异深挖 — 字段集/校验/行为对比 v2"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

c, r = api("POST", "/v1/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ})
if c != 200:
    log('create fail %s' % r[:200]); sys.exit(1)
sb_id = json.loads(r)['sandbox']['id']
log('sb_id=%s' % sb_id)
time.sleep(3)

B = "/v1/sandboxes/%s/cmd?teamId=%s" % (sb_id, TEAM)

def t(tag, body):
    c2, r2 = api("POST", B, body, 25)
    log('[%s] http=%s | %s' % (tag, c2, (r2[:220] if r2 else '').replace(chr(10), ' ')))

log('===== v1 cmd body matrix =====')
t('no-timeout', {"command": "id", "args": []})
t('minimal', {"command": "id"})
t('args-only', {"args": []})
t('with-wait', {"command": "id", "args": [], "wait": True})
t('with-logs', {"command": "id", "args": [], "logs": True})
t('with-cwd', {"command": "id", "args": [], "cwd": "/"})
t('with-env', {"command": "env", "args": [], "env": {"FOO": "bar"}})
t('with-shell', {"command": "id", "args": [], "shell": "bash"})
t('with-stdin', {"command": "cat", "args": [], "stdin": "hello"})
t('command-array', {"command": ["id"], "args": []})
t('b64-cmd', {"command": "aWQ=", "args": [], "encoding": "base64"})

log('')
log('===== v1 GET authz quick =====')
for q in ["?teamId=%s" % TEAM, "?teamId=team_BAD", ""]:
    c2, r2 = api("GET", "/v1/sandboxes/%s%s" % (sb_id, q), None, 25)
    log('GET %-18s -> %s | %s' % (q or '(none)', c2, (r2[:100] if r2 else '').replace(chr(10), ' ')))

api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (sb_id, TEAM, PROJ))
log('DONE')
