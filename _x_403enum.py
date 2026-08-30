# -*- coding: utf-8 -*-
"""403 authority-mismatch 触发条件枚举: deny-all / allow-all / custom 组合"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

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
    print('[%s] %s' % (tag, out[:150]), flush=True)

sid = get_sandbox('tinj1')
print('tinj1 sid:', sid, flush=True)

C1 = 'curl -s -o /dev/null -w "C1:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: httpbin.org" 2>&1 | head -1'
C2 = 'curl -s -o /dev/null -w "C2:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: 1.1.1.1" 2>&1 | head -1'
C3 = 'curl -s -o /dev/null -w "C3:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: example.com" 2>&1 | head -1'
C4 = 'curl -s -o /dev/null -w "C4:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: vercel.com" 2>&1 | head -1'

cases = [
    ('P1-deny-all', {"mode": "deny-all"}),
    ('P2-allow-all', {"mode": "allow-all"}),
    ('P3-allow-httpbin', {"mode": "custom", "allowedDomains": ["httpbin.org"]}),
    ('P4-allow-vercel', {"mode": "custom", "allowedDomains": ["vercel.com"]}),
    ('P5-httpbin+denyCIDR', {"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": ["1.1.1.0/24"]}),
    ('P6-httpbin+allowCIDR', {"mode": "custom", "allowedDomains": ["httpbin.org"], "allowedCIDRs": ["8.8.8.0/24"]}),
]
for tag, body in cases:
    set_policy(sid, body, tag)
    run(sid, tag + '-H-ok', C1)
    run(sid, tag + '-H-ip', C2)
    run(sid, tag + '-H-dom', C3)
    run(sid, tag + '-H-vercel', C4)
    time.sleep(0.5)

print('=== 403ENUM DONE ===', flush=True)
