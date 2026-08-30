# -*- coding: utf-8 -*-
"""v45d3: POST snapshot 201 是否导致 sandbox 执行层停止? 
流程: 创建 -> cmd 基线 -> POST snapshot -> 跟踪 status + cmd 可用性"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'snapstop48'

def api_raw(method, path, body=None, timeout=120):
    req = urllib.request.Request('https://api.vercel.com' + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
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

def get_status(tag):
    c, r = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    try:
        d = json.loads(r)
        print('[%s] status=%s' % (tag, d['sandbox'].get('status')), flush=True)
        return d['sandbox'].get('status')
    except Exception:
        print('[%s GET] -> %d %s' % (tag, c, (r or '')[:120]), flush=True)
        return None

if __name__ == '__main__':
    sid = mk()
    print('sid =', sid, flush=True)
    time.sleep(10)

    b64 = base64.b64encode(b'echo alive-before-snap').decode()
    c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=15000)
    print('[cmd before] -> %d out=%r' % (c, parse_data(r).strip()[:60]), flush=True)
    get_status('before')

    print('=== POST snapshot ===', flush=True)
    c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/snapshot?teamId=%s' % (sid, TEAM), {})
    print('[snapshot] -> %d %s' % (c, (r or '')[:200]), flush=True)

    for wait in [2, 5, 10]:
        time.sleep(wait)
        st = get_status('t+%ds' % wait)
        if wait == 10:
            c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=15000)
            print('[cmd after snap] -> %d out=%r' % (c, parse_data(r).strip()[:60]), flush=True)
            # network-policy 空 body (v45d 当时 410 的触发条件)
            c, r = api_raw('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), {})
            print('[np {} after snap] -> %d %s' % (c, (r or '')[:150]), flush=True)
            time.sleep(2)
            get_status('after-np')

    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
    print('CLEANED', flush=True)
