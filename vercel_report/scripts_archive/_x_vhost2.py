# -*- coding: utf-8 -*-
"""查询自己的项目域名 (合规 PoC 用) + 沙箱内 Host 伪造验证"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

# 1. 项目域名
c, r = api('GET', '/v9/projects/%s/domains?teamId=%s' % (PROJ, TEAM))
print('[domains] http=%s' % c, flush=True)
try:
    dd = json.loads(r)
    for d in (dd.get('domains') or [])[:10]:
        print('  domain:', d.get('name'), 'verified:', d.get('verified'), flush=True)
except Exception as e:
    print('  parse err', e, r[:200], flush=True)

# 2. 沙箱恢复 + 测自己的域名
c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
if d['sandbox'].get('status') != 'running':
    c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    print('resumed sid:', sid, flush=True)
    time.sleep(5)

api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
    {"mode": "custom", "allowedDomains": ["vercel.com"]})
time.sleep(3)

def run(tag, sc):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=60000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:400]), flush=True)

# 3. Host: 自己的 vercel.app 域名 (若有)
run('W1-mydomain', 'curl -s -o /dev/null -w "MY_CODE:%{http_code}\\n" -m 8 --http1.1 https://vercel.com/ -H "Host: pccp-team.vercel.app" 2>&1 | head -2')
# 4. 对照: 直接访问自己的域名 (公网)
run('W2-direct', 'curl -s -o /dev/null -w "DIRECT_CODE:%{http_code}\\n" -m 8 https://pccp-team.vercel.app/ 2>&1 | head -2')
# 5. 其他探测 (仅状态码)
run('W3-api', 'curl -s -o /dev/null -w "API_CODE:%{http_code}\\n" -m 8 --http1.1 https://vercel.com/ -H "Host: api.vercel.com" 2>&1 | head -2')
run('W4-v0', 'curl -s -o /dev/null -w "V0_CODE:%{http_code}\\n" -m 8 --http1.1 https://vercel.com/ -H "Host: vercel.com" 2>&1 | head -2')

print('=== VHOST2 DONE ===', flush=True)
