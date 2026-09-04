# -*- coding: utf-8 -*-
"""v52a: image 参数测试 + ports 转发 host 端口探测
I1-I4: image 变体 (docker hub 名/URL/自定义)
P1-P4: ports 常见 host 端口 (docker 2375/2376, 9000, 8080, 5432) -> 确认纯 guest 转发"""
import json, sys, time, urllib.request, urllib.error
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

def try_img(tag, name, img):
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(1)
    body = {"projectId": PROJ, "name": name}
    if img:
        body["image"] = img
    c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM, body, timeout=240)
    msg = ''
    try:
        d = json.loads(r)
        if 'error' in d:
            msg = d['error'].get('message', '')[:100]
        elif 'sandbox' in d:
            msg = 'OK status=%s image=%s' % (d['sandbox'].get('status'), d['sandbox'].get('image'))
    except Exception:
        msg = r[:100]
    print('[%s image=%r] -> %d %s' % (tag, img, c, msg), flush=True)
    api_raw('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
    time.sleep(2)

if __name__ == '__main__':
    print('=== I: image 参数 ===', flush=True)
    try_img('I1', 'img51a', None)  # 基线 (默认 universal image)
    try_img('I2', 'img51b', 'nginx')
    try_img('I3', 'img51c', 'docker.io/library/ubuntu:22.04')
    try_img('I4', 'img51d', 'http://127.0.0.1:1/x.img')
    try_img('I5', 'img51e', 'registry.vercel.internal/universal')

    print('=== P: ports 常见 host 端口 ===', flush=True)
    for p in [2375, 2376, 9000, 5432]:
        api_raw('DELETE', '/v2/sandboxes/px51?teamId=%s&projectId=%s' % (TEAM, PROJ))
        time.sleep(1)
        c, r = api_raw('POST', '/v4/sandboxes?teamId=%s' % TEAM,
                       {"projectId": PROJ, "name": 'px51', "ports": [p]}, timeout=180)
        msg = ''
        try:
            d = json.loads(r)
            msg = d.get('error', {}).get('message', '')[:80]
        except Exception:
            msg = r[:80]
        print('[port %d] -> %d %s' % (p, c, msg), flush=True)
        if c == 200:
            # 拿 URL 测转发
            sb = json.loads(r)['sandbox']
            sid = sb['currentSessionId']
            time.sleep(6)
            c3, r3 = api_raw('GET', '/v2/sandboxes/sessions/%s?teamId=%s' % (sid, TEAM))
            try:
                routes = json.loads(r3).get('routes', [])
                for rt in routes:
                    if rt.get('port') == p:
                        u = rt['url']
                        try:
                            req = urllib.request.Request(u + '/', method='GET')
                            with urllib.request.urlopen(req, timeout=15) as rr:
                                print('  [%s/] -> %d %s' % (u, rr.status, rr.read().decode(errors='replace')[:60]), flush=True)
                        except urllib.error.HTTPError as e:
                            print('  [%s/] -> %d %s' % (u, e.code, e.read().decode(errors='replace')[:80]), flush=True)
                        except Exception as e:
                            print('  [%s/] -> EXC %s' % (u, str(e)[:80]), flush=True)
            except Exception:
                pass
            api_raw('DELETE', '/v2/sandboxes/px51?teamId=%s&projectId=%s' % (TEAM, PROJ))
            time.sleep(2)
    print('DONE', flush=True)
