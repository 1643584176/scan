# -*- coding: utf-8 -*-
"""v51e: ports 转发内部服务端口保留检查 + 公网 URL 结构
P0: 各端口保留情况 (23456 reserved_port 已发现)
P1: 正常端口 3000 的转发 URL 结构 + guest 内访问对照"""
import base64, json, sys, time, urllib.request, urllib.error
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

if __name__ == '__main__':
    print('=== P0: 各端口保留情况 ===', flush=True)
    for p in [26661, 23457, 23456, 3000]:
        c0, r0 = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                         {"projectId": PROJ, "name": 'ports51x', "ports": [p]}, timeout=180)
        msg = ''
        try:
            msg = json.loads(r0)['error']['message'][:80]
        except Exception:
            pass
        print('[port %d] -> %d %s' % (p, c0, msg), flush=True)
        if c0 == 200:
            api_raw('DELETE', '/v2/sandboxes/ports51x?teamId=%s&projectId=%s' % (TEAM, PROJ))
            time.sleep(2)

    print('=== P1: create sandbox ports 3000 ===', flush=True)
    api_raw('DELETE', '/v2/sandboxes/ports51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    time.sleep(2)
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                   {"projectId": PROJ, "name": 'ports51', "ports": [3000]}, timeout=180)
    print('[create] -> %d' % c, flush=True)
    if c != 200:
        print(r[:500], flush=True)
        sys.exit(1)
    data = json.loads(r)
    sb = data['sandbox']
    sid = sb['currentSessionId']
    print('sid =', sid, flush=True)
    print('sandbox keys:', sorted(sb.keys()), flush=True)
    for k, v in sb.items():
        if 'port' in k.lower() or 'url' in k.lower():
            print('  field %s = %s' % (k, json.dumps(v)[:300]), flush=True)
    time.sleep(8)

    # 1. guest 内起 httpd (对照)
    b64 = base64.b64encode(b'echo hi > /tmp/h.txt; (cd /tmp && python3 -m http.server 3000 >/dev/null 2>&1 &); sleep 2; curl -sS -m 5 -i http://127.0.0.1:3000/h.txt 2>&1 | head -12').decode()
    c2, r2 = api_raw('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM),
                     {"command": "sh", "args": ["-c", 'echo %s | base64 -d | sh' % b64],
                      "wait": True, "logs": True, "timeout": 30000}, timeout=60)
    out = ''
    for line in r2.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[guest 内直接访问]\n%s' % out.strip()[:400], flush=True)

    # 2. 公网 URL: 从 GET session 找
    print('=== P2: 公网 URL ===', flush=True)
    c3, r3 = api_raw('GET', '/v2/sandboxes/sessions/%s?teamId=%s' % (sid, TEAM))
    print('[get session] -> %d' % c3, flush=True)
    if c3 == 200:
        print('session json:', json.dumps(json.loads(r3))[:1200], flush=True)
    # 常见 URL 格式探测
    for pat in ['https://%s.vercel.run' % sid, 'https://sb-%s.vercel.run' % sid,
                'https://ports51-%s.vercel.run' % sid[:8]]:
        try:
            req = urllib.request.Request(pat + '/h.txt', method='GET')
            with urllib.request.urlopen(req, timeout=15) as rr:
                print('[%s] -> %d %s' % (pat, rr.status, rr.read().decode(errors='replace')[:100]), flush=True)
        except urllib.error.HTTPError as e:
            print('[%s] -> %d %s' % (pat, e.code, e.read().decode(errors='replace')[:100]), flush=True)
        except Exception as e:
            print('[%s] -> EXC %s' % (pat, str(e)[:80]), flush=True)
    api_raw('DELETE', '/v2/sandboxes/ports51?teamId=%s&projectId=%s' % (TEAM, PROJ))
    print('DONE', flush=True)
