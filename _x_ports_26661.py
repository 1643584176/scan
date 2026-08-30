# -*- coding: utf-8 -*-
"""v51f: ports 转发 26661 (interactive 服务) 公网访问
1. create ports:[26661] -> routes URL
2. 公网 HTTP GET/POST/OPTIONS
3. WebSocket 连接探测
4. 对照: 23457 (无服务端口) 转发行为"""
import base64, json, ssl, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

def api_raw(method, path, body=None, timeout=180, maxlen=200000):
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

def http_req(url, method='GET', timeout=15, body=None, headers=None):
    req = urllib.request.Request(url, method=method)
    req.add_header('User-Agent', 'v51f')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, data=body, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read().decode(errors='replace')[:500]
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors='replace')[:500]
    except Exception as e:
        return -1, {}, 'EXC %s' % str(e)[:100]

if __name__ == '__main__':
    print('=== F1: create ports 26661+23457 ===', flush=True)
    api_raw('DELETE', '/v2/sandboxes/ports66?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                   {"projectId": PROJ, "name": 'ports66', "ports": [26661, 23457]}, timeout=180)
    print('[create] -> %d' % c, flush=True)
    if c != 200:
        print(r[:300], flush=True)
        sys.exit(1)
    sb = json.loads(r)['sandbox']
    sid = sb['currentSessionId']
    c3, r3 = api_raw('GET', '/v2/sandboxes/sessions/%s?teamId=%s' % (sid, TEAM))
    routes = []
    if c3 == 200:
        d3 = json.loads(r3)
        routes = d3.get('routes', [])
        print('routes:', json.dumps(routes), flush=True)
    url26661 = None
    url23457 = None
    for rt in routes:
        if rt.get('port') == 26661:
            url26661 = rt['url']
        if rt.get('port') == 23457:
            url23457 = rt['url']
    print('url26661 =', url26661, flush=True)
    print('url23457 =', url23457, flush=True)
    time.sleep(8)

    print('=== F2: 公网 HTTP 探测 26661 ===', flush=True)
    for path in ['/', '/healthz', '/ws', '/v1', '/interactive']:
        s, h, b = http_req((url26661 or '') + path)
        print('[26661 GET %s] -> %d %s' % (path, s, b[:100]), flush=True)
    s, h, b = http_req(url26661 + '/', method='POST', body=b'{"cmd":"ls"}')
    print('[26661 POST /] -> %d %s' % (s, b[:100]), flush=True)
    s, h, b = http_req(url26661 + '/', method='OPTIONS')
    print('[26661 OPTIONS /] -> %d allow=%s' % (s, h.get('Allow', '')), flush=True)
    s, h, b = http_req(url26661 + '/', method='HEAD')
    print('[26661 HEAD /] -> %d %s' % (s, b[:100]), flush=True)

    print('=== F3: 对照 23457 (无服务) ===', flush=True)
    s, h, b = http_req((url23457 or '') + '/')
    print('[23457 GET /] -> %d %s' % (s, b[:100]), flush=True)

    print('=== F4: WebSocket 探测 26661 ===', flush=True)
    try:
        import websocket  # 可能未安装
        ws = websocket.create_connection((url26661 or '').replace('https://', 'wss://') + '/',
                                         timeout=15, header=['User-Agent: v51f'])
        print('[ws connect] -> OK', flush=True)
        ws.send(json.dumps({'type': 'hello'}))
        print('[ws send] -> %s' % ws.recv()[:200], flush=True)
        ws.close()
    except ImportError:
        print('[ws] websocket 库未安装, 跳过', flush=True)
    except Exception as e:
        print('[ws] EXC %s' % str(e)[:150], flush=True)

    # 清理
    api_raw('DELETE', '/v2/sandboxes/ports66?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
