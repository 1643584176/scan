# -*- coding: utf-8 -*-
"""L5④c: PATCH 200 是否真更新 networkPolicy (readback 全字段对比)"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

ECHO = 'sbx-echo-e29ca9cb.vercel.app'

api("DELETE", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(3)

def mk(name, np):
    for attempt in range(4):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": name, "networkPolicy": np}, 60)
        if c == 429:
            log('429 retry %d' % (attempt + 1)); time.sleep(8); continue
        break
    log('[create %s] -> %s' % (name, c))
    return json.loads(r)['sandbox']['currentSessionId'] if c == 200 else None

sid = mk('l36d', {"mode": "custom", "allowedDomains": [ECHO],
                  "injectionRules": [{"domain": ECHO, "headers": {"X-Orig": "1"}}]})
if not sid:
    sys.exit(1)

def readback(tag):
    c, r = api("GET", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ))
    d = json.loads(r)['sandbox']
    np = json.dumps(d.get('networkPolicy'))
    log('[%s] networkPolicy = %s' % (tag, np[:400]))
    return np

time.sleep(2)
readback('before-patch')

# PATCH: 改为不同的注入头 + 改名 (验证 PATCH 是否一般生效)
c, r = api("PATCH", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ),
           {"name": "l36d-renamed",
            "networkPolicy": {"mode": "custom", "allowedDomains": [ECHO],
                              "injectionRules": [{"domain": ECHO, "headers": {"X-Dyn": "9"}}]}}, 30)
log('[patch] -> %s | %s' % (c, (r or '')[:200].replace(chr(10), ' ')))
time.sleep(2)
readback('after-patch')

api("DELETE", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
