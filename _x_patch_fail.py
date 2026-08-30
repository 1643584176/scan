# -*- coding: utf-8 -*-
"""v52f: PATCH network-policy 128.0.0.0/1 -> 500 是否部分应用 (fail-open 检测)
1. create custom+allowedDomains:[httpbin.org] (严格策略基线)
2. guest 测出网基线 (httpbin 200, example.com 拦)
3. PATCH networkPolicy + allowedCIDRs:["128.0.0.0/1"] -> 500?
4. guest 再测出网 (如果 example.com 放行 = fail-open -> firewall bypass!)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=180, maxlen=50000):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:maxlen]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:maxlen]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def probe_net(tag, sid):
    probe = ('echo "== httpbin (应放行) =="; timeout 10 curl -4 -sS -m 8 -o /dev/null -w "code=%{http_code}" https://httpbin.org/ip 2>&1; echo; '
             'echo "== example.com (应拦) =="; timeout 10 curl -4 -sS -m 8 -o /dev/null -w "code=%{http_code} err=%{errormsg}" https://example.com/ 2>&1; echo')
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 45000}, timeout=120)
    print('[%s] %s' % (tag, parse_data(r2).strip()[:300]), flush=True)

if __name__ == '__main__':
    name = 'fail51'
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(3)
    # 重试创建 (429 恢复)
    sid = None
    for i in range(6):
        c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                       {"projectId": PROJ, "name": name,
                        "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
        print('[create] -> %d' % c, flush=True)
        if c == 200:
            sid = json.loads(r)['sandbox']['currentSessionId']
            break
        if c == 429:
            print('  429, wait 20s', flush=True)
            time.sleep(20)
    if not sid:
        sys.exit(1)
    time.sleep(8)
    probe_net('基线(策略生效)', sid)

    print('=== PATCH network-policy + 128.0.0.0/1 ===', flush=True)
    c2, r2 = api_raw('PATCH', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ),
                     {"networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"],
                                        "allowedCIDRs": ["128.0.0.0/1"]}})
    print('[PATCH 128.0.0.0/1] -> %d %s' % (c2, (r2 or '')[:200]), flush=True)
    time.sleep(4)
    probe_net('PATCH 后', sid)

    print('=== PATCH 恢复 (对照: 0.0.0.0/1 正常) ===', flush=True)
    c3, r3 = api_raw('PATCH', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ),
                     {"networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"],
                                        "allowedCIDRs": ["0.0.0.0/1"]}})
    print('[PATCH 0.0.0.0/1] -> %d %s' % (c3, (r3 or '')[:200]), flush=True)
    time.sleep(4)
    probe_net('PATCH 恢复后', sid)

    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    print('DONE', flush=True)
