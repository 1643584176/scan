# -*- coding: utf-8 -*-
"""T 线: 注入 header 转发路由验证 (SNI vs Host vs 连接目标)"""
import json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/tinj1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('tinj1 sid:', sid, 'status:', d['sandbox']['status'], flush=True)
if d['sandbox'].get('status') != 'running':
    c, r = api('GET', '/v2/sandboxes/tinj1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    print('resumed sid:', sid, flush=True)
    time.sleep(5)

tests = [
    ('T1 Host=eu.httpbin.org', 'curl -sk --max-time 10 https://httpbin.org/anything -H "Host: eu.httpbin.org" 2>&1 | head -30'),
    ('T2 Host=1.1.1.1', 'curl -sk --max-time 10 https://httpbin.org/anything -H "Host: 1.1.1.1" 2>&1 | head -30'),
    ('T3 Host=example.com', 'curl -sk --max-time 10 https://httpbin.org/anything -H "Host: example.com" 2>&1 | head -30'),
    ('T4 resolve-to-1.1.1.1', 'curl -sk --max-time 10 --resolve httpbin.org:443:1.1.1.1 https://httpbin.org/anything 2>&1 | head -30'),
    ('T5 no-sni-ip', 'curl -sk --max-time 10 https://1.1.1.1/ -H "Host: httpbin.org" 2>&1 | head -20'),
]
for tag, script in tests:
    c, r = cmd(sid, 'sh', ['-c', script], timeout_ms=40000)
    print('=== %s -> %d' % (tag, c), flush=True)
    # 提取 data
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                out += line
    print(out[:1000], flush=True)
    time.sleep(1)

print('=== T-ROUTE DONE ===', flush=True)
