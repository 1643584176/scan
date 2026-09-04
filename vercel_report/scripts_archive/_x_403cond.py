# -*- coding: utf-8 -*-
"""403 条件定位: tinj1 vs npol1 策略对照 + Host=1.1.1.1 交叉测试"""
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

def get_policy(sid, tag):
    c, r = api('GET', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM))
    print('[%s policy] http=%d' % (tag, c), flush=True)
    try:
        print('  ', r[:400], flush=True)
    except Exception:
        pass

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

# 1. 两个沙箱当前策略
s1 = get_sandbox('tinj1')
s2 = get_sandbox('npol1')
get_policy(s1, 'tinj1')
get_policy(s2, 'npol1')

# 2. 交叉测试: 两个沙箱上 Host=1.1.1.1 / example.com / 172.31.0.2
for tag, sid in [('tinj1', s1), ('npol1', s2)]:
    run(sid, '%s-A-ip1111' % tag,
        'curl -s -o /dev/null -w "A_CODE:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: 1.1.1.1" 2>&1 | head -2')
    run(sid, '%s-B-domain' % tag,
        'curl -s -o /dev/null -w "B_CODE:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: example.com" 2>&1 | head -2')
    run(sid, '%s-C-privip' % tag,
        'curl -s -o /dev/null -w "C_CODE:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: 172.31.0.2" 2>&1 | head -2')
    run(sid, '%s-D-vercel' % tag,
        'curl -s -o /dev/null -w "D_CODE:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: vercel.com" 2>&1 | head -2')

print('=== 403COND DONE ===', flush=True)
