# -*- coding: utf-8 -*-
"""L5⑤: PATCH 移除 injectionRules 语义 (有→无: 原注入规则是否仍生效)
区分: PATCH=merge(忽略 inj 字段, 原规则保留) vs replace(整体替换, inj 重建失败)
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

def parse_data(r):
    out = ''
    for line in (r or '').splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

ECHO = 'sbx-echo-e29ca9cb.vercel.app'

api("DELETE", "/v2/sandboxes/l37?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(3)

def mk(name, np):
    for attempt in range(6):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": name, "networkPolicy": np}, 60)
        if c == 429:
            log('429 retry %d' % (attempt + 1)); time.sleep(15); continue
        break
    log('[create %s] -> %s' % (name, c))
    return json.loads(r)['sandbox']['currentSessionId'] if c == 200 else None

def run(sid, tag, cmdline):
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c", cmdline],
                  "wait": True, "timeout": 20000, "logs": True}, 35)
    out = parse_data(r3)
    log('[%s] -> %s' % (tag, out[:300].replace(chr(10), ' ')))
    return out

def probe_inj(sid, tag):
    run(sid, tag, "curl -s -m 8 https://%s/ | grep -io 'x-orig[^,]*\\|x-dyn[^,]*' || echo NOINJ" % ECHO)

sid = mk('l37', {"mode": "custom", "allowedDomains": [ECHO],
                 "injectionRules": [{"domain": ECHO, "headers": {"X-Orig": "1"}}]})
if not sid:
    sys.exit(1)
time.sleep(3)
probe_inj(sid, 'before')

# PATCH: 不带 injectionRules (有→无)
c, r = api("PATCH", "/v2/sandboxes/l37?teamId=%s&projectId=%s" % (TEAM, PROJ),
           {"networkPolicy": {"mode": "custom", "allowedDomains": [ECHO]}}, 30)
log('[patch rm-inj] -> %s' % c)
time.sleep(3)
probe_inj(sid, 'after-rm')

api("DELETE", "/v2/sandboxes/l37?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
