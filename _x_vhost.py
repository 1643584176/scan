# -*- coding: utf-8 -*-
"""虚拟主机混淆测试: allow vercel.com + Host 伪造 -> 边缘 vhost 路由?
V1: 基线 (SNI=vercel.com) -> 200?
V2: Host: www.vercel.com -> vhost 路由?
V3: Host: nonexist-abc123.vercel.app -> 404 (路由生效证明)
V4: h2 :authority 同样测试
V5: 若路由生效: HEAD 已知 vercel.app 站点 (仅状态码, 不读数据)
"""
import base64, json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, 'status:', d['sandbox']['status'], flush=True)
if d['sandbox'].get('status') != 'running':
    c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    print('resumed sid:', sid, flush=True)
    time.sleep(5)

def run(tag, sc, maxlen=900):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=90000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:maxlen]), flush=True)
    return out

# allow vercel.com
api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
    {"mode": "custom", "allowedDomains": ["vercel.com"]})
time.sleep(3)

run('V1-base', 'curl -s -o /dev/null -w "V1_CODE:%{http_code}\\n" -m 8 https://vercel.com/ 2>&1 | head -2')
run('V2-www', 'curl -s -o /dev/null -w "V2_CODE:%{http_code}\\n" -m 8 --http1.1 https://vercel.com/ -H "Host: www.vercel.com" 2>&1 | head -2')
run('V3-nonexist', 'curl -s -o /dev/null -w "V3_CODE:%{http_code}\\n" -m 8 --http1.1 https://vercel.com/ -H "Host: nonexist-abc123xyz.vercel.app" 2>&1 | head -2')
run('V3b-nonexist2', 'curl -s -o /dev/null -w "V3b_CODE:%{http_code}\\n" -m 8 --http1.1 https://vercel.com/ -H "Host: made-up-site-98765.vercel.app" 2>&1 | head -2')
run('V3c-other', 'curl -s -o /dev/null -w "V3c_CODE:%{http_code}\\n" -m 8 --http1.1 https://vercel.com/ -H "Host: vercel.app" 2>&1 | head -2')

print('=== VHOST DONE ===', flush=True)
