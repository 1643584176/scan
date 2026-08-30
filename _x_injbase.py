# -*- coding: utf-8 -*-
"""注入基线: allow httpbin.org (无 transform) -> curl httpbin.org/anything 看默认注入的 headers
+ Host 伪造时注入是否跟随 (请求转发到 vhost, 用不存在域名 404 观察 vs 基线对比)"""
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
    print('[%s] %s' % (tag, out[:1200]), flush=True)

sid = get_sandbox('tinj1')
print('sid:', sid, flush=True)

# 1. 基线: allow httpbin.org, 无 transform
set_policy(sid, {"mode": "custom", "allowedDomains": ["httpbin.org"]}, 'BASE')
run(sid, 'BASE-any', 'curl -sk -m 10 https://httpbin.org/anything 2>&1 | grep -iE "vercel|authorization|oidc|token|x-" | head -20')

# 2. transform 注入格式1 (allow 结构)
body1 = {
    "mode": "custom",
    "allow": {
        "httpbin.org": [
            {"transform": [{"headers": {"Authorization": "Bearer INJMARK_9f31a2c7"}}]}
        ],
        "*": []
    }
}
set_policy(sid, body1, 'T1-allow-transform')
run(sid, 'T1-any', 'curl -sk -m 10 https://httpbin.org/anything 2>&1 | grep -iE "authorization|INJMARK" | head -5')

# 3. 恢复 allow httpbin.org 简单模式, 测 Host 伪造对 httpbin 回显的影响 (应 404/308 不到 httpbin)
set_policy(sid, {"mode": "custom", "allowedDomains": ["httpbin.org"]}, 'BASE2')
run(sid, 'BASE2-fakehost', 'curl -s -o /dev/null -w "CODE:%{http_code}\\n" -m 8 --http1.1 https://httpbin.org/anything -H "Host: nonexist-abc123xyz.vercel.app" 2>&1 | head -2')

print('=== INJBASE DONE ===', flush=True)
