# -*- coding: utf-8 -*-
"""Forbidden 判定矩阵: SNI=api.vercel.com + 各种 Host 变体
区分: 404(无此vhost) vs 307/308(重定向) vs Forbidden(拒绝) vs 200(放行)
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
    print('[%s] %s' % (tag, out[:250]), flush=True)

sid = get_sandbox('tinj1')
print('sid:', sid, flush=True)

set_policy(sid, {"mode": "custom", "allowedDomains": ["api.vercel.com"]}, 'ALLOW-API')

tests = [
    ('1-base-api', 'https://api.vercel.com/anything', 'api.vercel.com'),
    ('2-nonexist', 'https://api.vercel.com/anything', 'nonexist-abc123xyz.vercel.app'),
    ('3-vercelcom', 'https://api.vercel.com/anything', 'vercel.com'),
    ('4-www', 'https://api.vercel.com/anything', 'www.vercel.com'),
    ('5-vercelapp', 'https://api.vercel.com/anything', 'vercel.app'),
    ('6-echo', 'https://api.vercel.com/anything', ECHO),
    ('7-echo-dep', 'https://api.vercel.com/anything', ECHO2),
    ('8-example', 'https://api.vercel.com/anything', 'example.com'),
    ('9-ip', 'https://api.vercel.com/anything', '1.1.1.1'),
    ('10-www-vercelapp', 'https://api.vercel.com/anything', 'www.vercel.app'),
]
for tag, url, host in tests:
    sc = ('curl -s -o /dev/null -w "%%{http_code}" -m 10 --http1.1 %s -H "Host: %s" 2>&1 | head -1' % (url, host))
    run(sid, tag, sc)

# 补充: SNI=vercel.com 下的对照
set_policy(sid, {"mode": "custom", "allowedDomains": ["vercel.com"]}, 'ALLOW-VERCEL')
tests2 = [
    ('A-echo', 'https://vercel.com/anything', ECHO),
    ('B-nonexist', 'https://vercel.com/anything', 'nonexist-abc123xyz.vercel.app'),
    ('C-vercelapp', 'https://vercel.com/anything', 'vercel.app'),
    ('D-www', 'https://vercel.com/anything', 'www.vercel.com'),
]
for tag, url, host in tests2:
    sc = ('curl -s -o /dev/null -w "%%{http_code}" -m 10 --http1.1 %s -H "Host: %s" 2>&1 | head -1' % (url, host))
    run(sid, tag, sc)

print('=== FB MATRIX DONE ===', flush=True)
