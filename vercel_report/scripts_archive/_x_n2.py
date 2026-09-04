# -*- coding: utf-8 -*-
"""独立根因候选2: 项目 OIDC token 是否泄露到 sandbox guest (先看项目配置+字段)"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

# 1) 项目全字段 + OIDC 配置
c, r = api("GET", "/v9/projects/%s" % PROJ)
log('GET /v9/projects -> %s' % c)
if c == 200:
    d = json.loads(r)
    oidc = d.get('oidcTokenConfig')
    log('oidcTokenConfig: %s' % json.dumps(oidc))
    log('')
    log('--- project fields ---')
    for k in sorted(d.keys()):
        v = d[k]
        s = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
        log('  %s: %s' % (k, s[:180]))
