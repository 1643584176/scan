# -*- coding: utf-8 -*-
"""决定性对照: 公网直连 vs 沙箱内 Host 伪造, 响应是否一致?
一致 -> 上游应用/边缘自身防护, 沙箱无新增攻击面, H 线关闭
不一致 -> 沙箱路径存在差异, 深挖
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
    print('[%s] %s' % (tag, out[:400]), flush=True)

sid = get_sandbox('tinj1')
print('sid:', sid, flush=True)

# 本地公网对照 (本机网络)
import subprocess
def pub(tag, url, host=None):
    args = ['curl', '-sk', '-m', '10', '-o', '/dev/null', '-w', '%{http_code} loc:%{redirect_url}', url]
    if host:
        args += ['-H', 'Host: ' + host]
    r = subprocess.run(args, capture_output=True, text=True)
    print('[PUB-%s] %s' % (tag, r.stdout.strip()[:200]), flush=True)

pub('A-vercelcom', 'https://api.vercel.com/anything', 'vercel.com')
pub('B-nonexist', 'https://api.vercel.com/anything', 'nonexist-abc123xyz.vercel.app')
pub('C-echo', 'https://api.vercel.com/anything', ECHO)
pub('D-echo-dep', 'https://api.vercel.com/anything', ECHO2)
pub('E-base', 'https://api.vercel.com/anything', 'api.vercel.com')
pub('F-www-vercelcom', 'https://vercel.com/anything', 'www.vercel.com')
pub('G-nonexist2', 'https://vercel.com/anything', 'nonexist-abc123xyz.vercel.app')
pub('H-echo2', 'https://vercel.com/anything', ECHO)
pub('I-vercelapp', 'https://vercel.com/anything', 'vercel.app')
pub('J-www2', 'https://vercel.com/anything', 'www.vercel.com')
pub('K-vercelcom-root', 'https://vercel.com/', 'vercel.com')
pub('L-ip', 'https://api.vercel.com/anything', '1.1.1.1')

# 沙箱内同组 (api.vercel.com 组)
set_policy(sid, {"mode": "custom", "allowedDomains": ["api.vercel.com"]}, 'ALLOW-API')
for tag, host in [('S-A-vercelcom', 'vercel.com'), ('S-B-nonexist', 'nonexist-abc123xyz.vercel.app'),
                  ('S-C-echo', ECHO), ('S-D-echo-dep', ECHO2), ('S-E-base', 'api.vercel.com'), ('S-L-ip', '1.1.1.1')]:
    sc = ('curl -s -o /dev/null -w "%%{http_code} loc:%%{redirect_url}" -m 10 --http1.1 https://api.vercel.com/anything -H "Host: %s" 2>&1 | head -1' % host)
    run(sid, tag, sc)

# 沙箱内 (vercel.com 组)
set_policy(sid, {"mode": "custom", "allowedDomains": ["vercel.com"]}, 'ALLOW-VERCEL')
for tag, host in [('S-F-www', 'www.vercel.com'), ('S-G-nonexist2', 'nonexist-abc123xyz.vercel.app'),
                  ('S-H-echo2', ECHO), ('S-I-vercelapp', 'vercel.app'), ('S-J-www2', 'www.vercel.com')]:
    sc = ('curl -s -o /dev/null -w "%%{http_code} loc:%%{redirect_url}" -m 10 --http1.1 https://vercel.com/anything -H "Host: %s" 2>&1 | head -1' % host)
    run(sid, tag, sc)

print('=== PUB vs SBX DONE ===', flush=True)
