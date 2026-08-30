# -*- coding: utf-8 -*-
"""L5④b 补跑: PATCH /v2/sandboxes/{name}?projectId= 动态更新 networkPolicy"""
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

def run(sid, tag, cmdline):
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c", cmdline],
                  "wait": True, "timeout": 20000, "logs": True}, 35)
    out = parse_data(r3)
    log('[%s] -> %s' % (tag, out[:400].replace(chr(10), ' ')))
    return out

sid = mk('l36d', {"mode": "custom", "allowedDomains": [ECHO]})
if not sid:
    sys.exit(1)
time.sleep(3)
run(sid, 'before-patch', "curl -s -m 8 https://%s/ | grep -o 'X-Dyn[^,]*' || echo NODYN" % ECHO)

# 带 projectId 的 PATCH
c, r = api("PATCH", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ),
           {"networkPolicy": {"mode": "custom", "allowedDomains": [ECHO],
                              "injectionRules": [{"domain": ECHO, "headers": {"X-Dyn": "1"}}]}}, 30)
log('[patch v2+projectId] -> %s | %s' % (c, (r or '')[:250].replace(chr(10), ' ')))
if c == 200:
    # readback: GET 确认 networkPolicy 是否更新
    c2, r2 = api("GET", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ))
    log('[readback] -> %s | %s' % (c2, (r2 or '')[:300].replace(chr(10), ' ')))
    time.sleep(3)
    run(sid, 'after-patch', "curl -s -m 8 https://%s/ | grep -o 'X-Dyn[^,]*' || echo NODYN" % ECHO)

api("DELETE", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
