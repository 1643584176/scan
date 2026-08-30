# -*- coding: utf-8 -*-
"""v52b: guest 内 23456/26661 底层协议探测
T1: 裸 TCP banner
T2: HTTP/2 prior knowledge (h2c)
T3: gRPC health check + reflection
T4: 响应头细节"""
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

if __name__ == '__main__':
    api_raw('DELETE', '/v2/sandboxes/grpc51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": 'grpc51'})
    if c != 200:
        print('create failed', r[:200], flush=True)
        sys.exit(1)
    sid = json.loads(r)['sandbox']['currentSessionId']
    print('sid =', sid, flush=True)
    time.sleep(8)

    # guest 内探测脚本 (base64 传输避免转义问题)
    probe = r'''
set -x
echo "=== T1: 裸 TCP banner 23456 ==="
timeout 4 bash -c 'exec 3<>/dev/tcp/127.0.0.1/23456; head -c 200 <&3 | xxd | head -10' 2>&1 || echo "no banner"
echo "=== T1b: 裸 TCP banner 26661 ==="
timeout 4 bash -c 'exec 3<>/dev/tcp/127.0.0.1/26661; head -c 200 <&3 | xxd | head -10' 2>&1 || echo "no banner"
echo "=== T2: h2c prior knowledge 23456 ==="
curl -sS -m 5 --http2-prior-knowledge -i http://127.0.0.1:23456/ 2>&1 | head -10
echo "=== T2b: h2c 26661 ==="
curl -sS -m 5 --http2-prior-knowledge -i http://127.0.0.1:26661/ 2>&1 | head -10
echo "=== T3: gRPC health 23456 ==="
curl -sS -m 5 -i -X POST http://127.0.0.1:23456/grpc.health.v1.Health/Check -H 'content-type: application/grpc' --data-binary $'\x00\x00\x00\x00\x00' 2>&1 | head -10
echo "=== T3b: gRPC health 26661 ==="
curl -sS -m 5 -i -X POST http://127.0.0.1:26661/grpc.health.v1.Health/Check -H 'content-type: application/grpc' --data-binary $'\x00\x00\x00\x00\x00' 2>&1 | head -10
echo "=== T4: HTTP 响应头细节 23456 ==="
curl -sS -m 5 -i -X OPTIONS http://127.0.0.1:23456/ 2>&1 | head -15
echo "=== T5: 端口监听状态 ==="
ss -tlnp 2>/dev/null | grep -E '23456|26661' || netstat -tlnp 2>/dev/null | grep -E '23456|26661'
echo "=== T6: 进程 ==="
ps aux 2>/dev/null | grep -iE '23456|26661|sandbox|init' | grep -v grep | head -10
'''
    b64 = base64.b64encode(probe.encode()).decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "bash", "args": ["-c", 'echo %s | base64 -d | bash' % b64],
                      "wait": True, "logs": True, "timeout": 60000}, timeout=120)
    print('[probe] -> %d' % c2, flush=True)
    print(parse_data(r2)[:2500], flush=True)
    api_raw('DELETE', '/v2/sandboxes/grpc51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
