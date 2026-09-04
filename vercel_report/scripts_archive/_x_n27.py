# -*- coding: utf-8 -*-
"""非传统面I: 版本差异 — ①v3 创建字段接受度(v4 拒绝的字段) ②v1 端点全集 ③resume 前后 ports URL 变化"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

# ① v3 创建: 带 v4 拒绝的字段
log('===== ① v3 字段接受度 =====')
for tag, body in [
    ('v3-s3key', {"projectId": PROJ, "name": "n27a", "networkPolicy": {"mode": "allow-all", "s3Key": "x.json"}}),
    ('v3-ports', {"projectId": PROJ, "name": "n27a", "ports": [8080]}),
    ('v3-inj', {"projectId": PROJ, "name": "n27a", "networkPolicy": {"mode": "custom",
                "allowedDomains": ["httpbin.org"], "injectionRules": [{"domain": "httpbin.org", "headers": {"X-T": "1"}}]}}),
    ('v3-env', {"projectId": PROJ, "name": "n27a", "env": {"FOO": "bar"}}),
]:
    api("DELETE", "/v2/sandboxes/n27a?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(1)
    c, r = api("POST", "/v3/sandboxes?teamId=%s" % TEAM, body, 60)
    log('[%s] -> %s | %s' % (tag, c, (r or '')[:250].replace(chr(10), ' ')))
    if c == 200:
        api("DELETE", "/v2/sandboxes/n27a?teamId=%s&projectId=%s" % (TEAM, PROJ))
        time.sleep(1)

# ② v1 端点全集 (之前只测 cmd/env)
log('')
log('===== ② v1 行为 =====')
api("DELETE", "/v2/sandboxes/n27b?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v1/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n27b"}, 60)
log('v1 create -> %s | %s' % (c, (r or '')[:250].replace(chr(10), ' ')))
if c == 200:
    sid = json.loads(r)['sandbox']['id']
    for p in ["/v1/sandboxes/%s/stop" % sid, "/v1/sandboxes/%s/snapshot" % sid,
              "/v1/sandboxes/%s/network-policy" % sid, "/v1/sandboxes/%s/fs/read" % sid,
              "/v1/sandboxes/%s/interactive" % sid]:
        c2, r2 = api("POST", p + "?teamId=%s" % TEAM, {} if 'stop' in p else ({"path": "/etc/passwd"} if 'fs' in p else {}), 15)
        log('[v1 %s] -> %s | %s' % (p.split('/')[-1], c2, (r2 or '')[:150].replace(chr(10), ' ')))
    api("DELETE", "/v2/sandboxes/n27b?teamId=%s&projectId=%s" % (TEAM, PROJ))

# ③ resume 前后 ports URL
log('')
log('===== ③ ports URL 跨 resume =====')
api("DELETE", "/v2/sandboxes/n27c?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "n27c", "ports": [8080]}, 60)
log('create ports -> %s' % c)
routes1 = None
if c == 200:
    try: routes1 = json.loads(r)['sandbox'].get('routes')
    except Exception: pass
    log('routes1: %s' % json.dumps(routes1)[:200])
    sid = json.loads(r)['sandbox']['currentSessionId']
    time.sleep(2)
    # guest 起服务
    api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
        {"command": "sh", "args": ["-c", "nohup python3 -m http.server 8080 >/dev/null 2>&1 &"], "wait": True, "timeout": 8000}, 25)
    time.sleep(3)
    if routes1:
        u = routes1[0]['url']
        c2, r2 = api("GET", "/v2/sandboxes/n27c?teamId=%s&projectId=%s&resume=true" % (TEAM, PROJ), None, 30)
        routes2 = None
        try: routes2 = json.loads(r2)['sandbox'].get('routes')
        except Exception: pass
        log('resume routes2: %s' % json.dumps(routes2)[:200])
        # 旧 URL 与新 URL 可达性 (仅 TCP connect 指纹, 合规)
        import urllib.request
        for tag, url in [('old', u), ('new', routes2[0]['url'] if routes2 else None)]:
            if not url: continue
            try:
                rr = urllib.request.urlopen(url + '/', timeout=8)
                log('[%s url] -> %s' % (tag, rr.status))
                rr.close()
            except Exception as e:
                log('[%s url] err %s' % (tag, str(e)[:80]))
    api("DELETE", "/v2/sandboxes/n27c?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
