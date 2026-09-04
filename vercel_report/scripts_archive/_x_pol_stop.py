# -*- coding: utf-8 -*-
"""v45d2: network-policy 空 body 是否触发 sandbox 停止? (P2 410 复现)
流程: 创建 -> 确认 alive -> POST network-policy {} -> 跟踪 sandbox/session 状态 + cmd 可用性
同时验证手动 snapshot 201 端点 (P1 发现)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'polstop47'

def api_raw(method, path, body=None, ctype='application/json', timeout=90):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    if ctype:
        req.add_header('Content-Type', ctype)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode(errors='replace')[:800]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:800]
    except Exception as e:
        return -1, 'EXC %s' % str(e)[:120]

def mk():
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    time.sleep(3)
    for attempt in range(8):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 60)
        if c == 429:
            print('[create] 429 retry', flush=True)
            time.sleep(20)
            continue
        break
    print('[create] -> %s' % c, flush=True)
    if c != 200:
        sys.exit(1)
    return json.loads(r)['sandbox']['currentSessionId']

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
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(10)

    # 基线: sandbox 状态 + cmd 可用
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        print('[GET sandbox] status=%s np=%s' % (d['sandbox'].get('status'), d['sandbox'].get('networkPolicy')), flush=True)
    except Exception:
        print('[GET sandbox] -> %d %s' % (c, (r or '')[:150]), flush=True)
    b64 = base64.b64encode(b'echo alive-mark-1').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=15000)
    print('[cmd baseline] -> %d out=%r' % (c, parse_data(r).strip()[:60]), flush=True)

    # 核心: POST network-policy 空 body
    print('=== POST network-policy {} ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), {})
    print('[np {}] -> %d %s' % (c, (r or '')[:200]), flush=True)

    # 跟踪状态 1/5/15s
    for wait in [1, 5, 15]:
        time.sleep(wait)
        c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
        try:
            d = json.loads(r)
            st = d['sandbox'].get('status')
            print('[t+%ds] sandbox.status=%s' % (wait, st), flush=True)
        except Exception:
            print('[t+%ds GET] -> %d %s' % (wait, c, (r or '')[:120]), flush=True)
        if wait == 15:
            c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=15000)
            print('[cmd after] -> %d out=%r' % (c, parse_data(r).strip()[:60]), flush=True)

    # 对照: 正常 body 再试 (如果 sandbox 还活着)
    print('=== POST network-policy 正常 body ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM),
                   {"mode": "custom", "allowedDomains": ["httpbin.org"]})
    print('[np custom] -> %d %s' % (c, (r or '')[:200]), flush=True)
    time.sleep(2)
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=15000)
    print('[cmd after custom] -> %d out=%r' % (c, parse_data(r).strip()[:60]), flush=True)

    # 对照: 正常 body 再试 (如果 sandbox 还活着)
    print('=== POST network-policy 空 body 再次 (同 sandbox) ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), {})
    print('[np {} x2] -> %d %s' % (c, (r or '')[:200]), flush=True)
    time.sleep(3)
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        print('[final] sandbox.status=%s' % d['sandbox'].get('status'), flush=True)
    except Exception:
        print('[final GET] -> %d %s' % (c, (r or '')[:120]), flush=True)

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
