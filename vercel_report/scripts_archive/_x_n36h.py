# -*- coding: utf-8 -*-
"""L5④e: PATCH 后 injectionRules 行为验证 (完整响应 + 大小写不敏感 grep)
① PATCH 前: X-Orig 注入到 echo 是否生效 (grep -i 修正)
② PATCH 后: X-Dyn 注入到 echo 是否生效 (allowedDomains 改回 echo)
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
    log('[%s] -> %s' % (tag, out[:600].replace(chr(10), ' ')))
    return out

sid = mk('l36d', {"mode": "custom", "allowedDomains": [ECHO],
                  "injectionRules": [{"domain": ECHO, "headers": {"X-Orig": "1"}}]})
if not sid:
    sys.exit(1)
time.sleep(3)

# ① PATCH 前: 完整响应检查 X-Orig
run(sid, 'before-full', "curl -s -m 8 https://%s/ | grep -io 'x-orig[^,]*' || echo NOXORIG" % ECHO)

# ② PATCH: allowedDomains 保持 echo, 注入头换成 X-Dyn
c, r = api("PATCH", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ),
           {"networkPolicy": {"mode": "custom", "allowedDomains": [ECHO],
                              "injectionRules": [{"domain": ECHO, "headers": {"X-Dyn": "9"}}]}}, 30)
log('[patch] -> %s' % c)
time.sleep(3)
run(sid, 'after-full', "curl -s -m 8 https://%s/ | grep -io 'x-dyn[^,]*' || echo NOXDYN" % ECHO)

api("DELETE", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
