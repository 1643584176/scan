# -*- coding: utf-8 -*-
"""v52c: allowedCIDRs 绕过 deny-all 测试 (firewall bypass 面)
S1: deny-all + allowedCIDRs:["0.0.0.0/0"] -> 公网可达?
S2: deny-all + allowedCIDRs:["0.0.0.0/1","128.0.0.0/1"] (全 IPv4)
S3: deny-all + allowedCIDRs:["::/0"] (全 IPv6)
S4: deny-all + allowedCIDRs:["10.0.0.0/8"] (对照: 私有网段)
S5: allow-all + deniedCIDRs:["0.0.0.0/0"] (对照: deniedCIDRs 全拦?)
S6: 基线 deny-all (对照)"""
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

def test_policy(tag, name, policy):
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": name, "networkPolicy": policy}
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, body)
    print('[%s create] -> %d' % (tag, c), flush=True)
    if c != 200:
        try:
            print('  err:', json.loads(r).get('error', {}).get('message', r[:120]), flush=True)
        except Exception:
            print('  err:', r[:120], flush=True)
        return
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(8)
    # guest 内测出网: DNS + TCP + UDP
    probe = ('echo "== DNS =="; timeout 6 getent hosts example.com 2>&1 | head -2; '
             'echo "== TCP =="; timeout 8 curl -sS -m 6 -o /dev/null -w "%{http_code}" https://example.com/ 2>&1; echo; '
             'echo "== TCP_IP =="; timeout 8 curl -sS -m 6 -o /dev/null -w "%{http_code}" http://93.184.215.14/ 2>&1; echo; '
             'echo "== DNS_DIRECT =="; timeout 8 curl -sS -m 6 -o /dev/null -w "%{http_code}" https://93.184.215.14/ -H "Host: example.com" 2>&1; echo')
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 45000}, timeout=120)
    out = parse_data(r2).strip()
    print('  %s' % out.replace('\n', '\n  ')[:600], flush=True)
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(2)

if __name__ == '__main__':
    # custom 模式 + CIDR 组合
    test_policy('C1', 'cidr51a', {"mode": "custom", "allowedCIDRs": ["0.0.0.0/0"]})
    test_policy('C2', 'cidr51b', {"mode": "custom", "allowedCIDRs": ["0.0.0.0/1", "128.0.0.0/1"]})
    test_policy('C3', 'cidr51c', {"mode": "custom", "allowedCIDRs": ["::/0"]})
    test_policy('C4', 'cidr51d', {"mode": "custom", "allowedDomains": ["example.com"]})
    test_policy('C5', 'cidr51e', {"mode": "custom", "allowedDomains": ["example.com"], "allowedCIDRs": ["0.0.0.0/0"]})
    test_policy('C6', 'cidr51f', {"mode": "custom", "allowedDomains": ["*"], "allowedCIDRs": ["0.0.0.0/0"]})
    test_policy('C7', 'cidr51g', {"mode": "custom", "allowedDomains": ["*.example.com"], "allowedCIDRs": ["10.0.0.0/8"]})
    print('DONE', flush=True)
