# -*- coding: utf-8 -*-
"""403 条件定位 v2: tinj1 vs npol1 同策略 (allow httpbin.org) + Host 矩阵对照"""
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

def set_policy(sid, body):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
    print('  set_policy http=%d' % c, flush=True)
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
    print('[%s] %s' % (tag, out[:200]), flush=True)

s1 = get_sandbox('tinj1')
s2 = get_sandbox('npol1')
print('tinj1 sid:', s1, flush=True)
print('npol1 sid:', s2, flush=True)

# 两个沙箱都设置 allow httpbin.org
set_policy(s1, {"mode": "custom", "allowedDomains": ["httpbin.org"]})
set_policy(s2, {"mode": "custom", "allowedDomains": ["httpbin.org"]})

matrix = [
    ('E-host-ok', 'curl -s -o /dev/null -w "E:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: httpbin.org" 2>&1 | head -2'),
    ('A-ip1111', 'curl -s -o /dev/null -w "A:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: 1.1.1.1" 2>&1 | head -2'),
    ('B-domain', 'curl -s -o /dev/null -w "B:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: example.com" 2>&1 | head -2'),
    ('C-privip', 'curl -s -o /dev/null -w "C:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: 172.31.0.2" 2>&1 | head -2'),
    ('D-vercel', 'curl -s -o /dev/null -w "D:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: vercel.com" 2>&1 | head -2'),
    ('F-subdom', 'curl -s -o /dev/null -w "F:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: eu.httpbin.org" 2>&1 | head -2'),
    ('G-nohost', 'curl -s -o /dev/null -w "G:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host:" 2>&1 | head -2'),
]
for tag, sid in [('tinj1', s1), ('npol1', s2)]:
    print('===== %s =====' % tag, flush=True)
    for t, sc in matrix:
        run(sid, '%s-%s' % (tag, t), sc)
        time.sleep(0.5)

print('=== 403COND2 DONE ===', flush=True)
