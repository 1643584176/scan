# -*- coding: utf-8 -*-
"""非传统面L3: injectionRules 逐头验证 (echo 回显 + 落盘)
① 敏感头名逐个注入: Host / Authorization / X-Forwarded-For / x-vercel-* / Cookie / X-Api-Key
② 多值头 (数组值 → 重复头?)
③ custom 模式 OIDC 自动注入确认 (落盘)
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

def mk_sandbox(name, headers):
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
    time.sleep(2)
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {
        "projectId": PROJ, "name": name,
        "networkPolicy": {"mode": "custom", "allowedDomains": [ECHO],
                          "injectionRules": [{"domain": ECHO, "headers": headers}]},
    }, 60)
    log('[create %s] -> %s | %s' % (name, c, (r or '')[:200].replace(chr(10), ' ')))
    return c, r

def probe(sid, tag, cmdline):
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c", cmdline],
                  "wait": True, "timeout": 20000, "logs": True}, 35)
    out = parse_data(r3)
    # 落盘双通道
    api("POST", "/v2/sandboxes/sessions/%s/fs/write?teamId=%s" % (sid, TEAM),
        None, 10)  # noop
    log('[%s] -> %s' % (tag, out[:500].replace(chr(10), ' ')))
    return out

# ===== ① 敏感头逐个 =====
log('===== ① 敏感头逐个 =====')
for hname, hval in [
    ('Host', 'vercel.com'),
    ('Authorization', 'Bearer FAKE123'),
    ('X-Forwarded-For', '6.6.6.6'),
    ('X-Vercel-OIDC-Token', 'FAKE_OIDC'),
    ('X-Real-IP', '9.9.9.9'),
    ('Cookie', 'session=evil'),
    ('X-Api-Key', 'sk-fake'),
    ('X-Vercel-Forwarded-For', '7.7.7.7'),
]:
    c, r = mk_sandbox('l32', {hname: hval})
    if c != 200:
        log('[%s] 400/other, skip' % hname)
        time.sleep(1)
        continue
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(3)
    probe(sid, hname,
          "curl -s -m 10 https://%s/ > /tmp/h.txt 2>&1; cat /tmp/h.txt" % ECHO)
    api("DELETE", "/v2/sandboxes/l32?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(1)

# ===== ② 多值头 =====
log('')
log('===== ② 多值头 =====')
c, r = mk_sandbox('l32b', {'X-Multi': ['v1', 'v2'], 'X-Auth2': ['Bearer A', 'Bearer B']})
if c == 200:
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(3)
    probe(sid, 'multi', "curl -s -m 10 https://%s/ > /tmp/m.txt 2>&1; cat /tmp/m.txt" % ECHO)
    api("DELETE", "/v2/sandboxes/l32b?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(1)

# ===== ③ OIDC custom 模式 =====
log('')
log('===== ③ OIDC custom =====')
c, r = mk_sandbox('l32c', {})
if c == 200:
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(3)
    probe(sid, 'oidc', "curl -s -m 10 https://%s/ > /tmp/o.txt 2>&1; cat /tmp/o.txt" % ECHO)
    api("DELETE", "/v2/sandboxes/l32c?teamId=%s&projectId=%s" % (TEAM, PROJ))

log('DONE')
