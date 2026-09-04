# -*- coding: utf-8 -*-
"""候选11c: ports 暴露 URL 公网可达性验证 (无认证?)"""
import json, sys, time, urllib.request, ssl
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n15c?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
           {"projectId": PROJ, "name": "n15c", "ports": [8080]}, 60)
d = json.loads(r)
routes = d.get('routes', [])
log('routes: %s' % json.dumps(routes))
sid = d['sandbox']['currentSessionId']
time.sleep(4)

c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "sh", "args": ["-c", "cd /tmp && echo PORT_TEST_2026 > f.txt && (python3 -m http.server 8080 >/dev/null 2>&1 &) && sleep 2 && curl -s -o /dev/null -w 'local=%{http_code}' http://127.0.0.1:8080/f.txt"],
            "wait": True, "timeout": 20000}, 40)
for line in r.splitlines():
    if '"data"' in line:
        try: log('  local: %s' % json.loads(line).get('data'))
        except Exception: pass

if routes:
    u = routes[0]['url'] + '/f.txt'
    log('public URL: %s' % u)
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            body = resp.read()
            log('public GET -> %s | %s' % (resp.status, body[:100]))
    except urllib.error.HTTPError as e:
        log('public GET -> HTTP %s | %s' % (e.code, e.read()[:100]))
    except Exception as e:
        log('public GET err: %s' % str(e)[:150])

api("DELETE", "/v2/sandboxes/n15c?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
