# -*- coding: utf-8 -*-
"""候选4e: v1/v2 cmd env 注入 — 用文件副作用验证 env 是否真正进入进程环境"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

# --- v1 ---
c, r = api("POST", "/v1/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ})
sb1 = json.loads(r)['sandbox']['id']
log('v1 sb=%s' % sb1)
time.sleep(3)
B1 = "/v1/sandboxes/%s/cmd?teamId=%s" % (sb1, TEAM)
c, r = api("POST", B1, {"command": "sh",
                        "args": ["-c", 'echo "FOO=$FOO OIDC=$VERCEL_OIDC_TOKEN" > /tmp/v1out.txt'],
                        "env": {"FOO": "v1bar", "VERCEL_OIDC_TOKEN": "v1pwn"}}, 25)
log('v1 cmd -> %s' % c)
time.sleep(2)
c, r = api("POST", "/v1/sandboxes/%s/fs/read?teamId=%s" % (sb1, TEAM), {"path": "/tmp/v1out.txt"}, 25)
log('v1 fs/read /tmp/v1out.txt -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))

# --- v2 ---
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n6b"})
sid2 = json.loads(r)['sandbox']['currentSessionId']
log('v2 sid=%s' % sid2)
time.sleep(3)
B2 = "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid2, TEAM)
c, r = api("POST", B2, {"command": "sh",
                        "args": ["-c", 'echo "FOO=$FOO OIDC=$VERCEL_OIDC_TOKEN" > /tmp/v2out.txt'],
                        "env": {"FOO": "v2bar", "VERCEL_OIDC_TOKEN": "v2pwn"},
                        "wait": True, "timeout": 10000}, 25)
log('v2 cmd -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))
time.sleep(2)
c, r = api("POST", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid2, TEAM), {"path": "/tmp/v2out.txt"}, 25)
log('v2 fs/read /tmp/v2out.txt -> %s | %s' % (c, (r[:200] if r else '').replace(chr(10), ' ')))

api("DELETE", "/v2/sandboxes/n6b?teamId=%s&projectId=%s" % (TEAM, PROJ))
api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (sb1, TEAM, PROJ))
log('DONE')
