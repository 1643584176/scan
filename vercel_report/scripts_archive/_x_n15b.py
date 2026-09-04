# -*- coding: utf-8 -*-
"""候选11b: ports 暴露 URL — routes 字段确认 + 公网访问验证"""
import json, sys, time, urllib.request
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n15b?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
           {"projectId": PROJ, "name": "n15b", "ports": [8080]}, 60)
log('create -> %s' % c)
d = json.loads(r)
log('resp keys: %s' % sorted(d.keys()))
for k in ['sandbox', 'session', 'routes']:
    if k in d:
        log('%s: %s' % (k, json.dumps(d[k])[:600]))
sid = d.get('session', {}).get('id') or d.get('sandbox', {}).get('currentSessionId')
log('sid=%s' % sid)
time.sleep(4)

# 起服务
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "sh", "args": ["-c", "cd /tmp && echo PORT_TEST_2026 > f.txt && (python3 -m http.server 8080 >/dev/null 2>&1 &) && sleep 2 && curl -s -o /dev/null -w 'local=%{http_code}' http://127.0.0.1:8080/f.txt"],
            "wait": True, "timeout": 20000}, 40)
log('serve -> %s' % c)
for line in r.splitlines():
    if '"data"' in line:
        try: log('  data: %s' % json.loads(line).get('data'))
        except Exception: pass

# routes 相关 GET 变体
for p in ["/v2/sandboxes/n15b?teamId=%s&projectId=%s" % (TEAM, PROJ),
          "/v2/sandboxes/sessions/%s?teamId=%s" % (sid, TEAM)]:
    c, r = api("GET", p, None, 20)
    try:
        d2 = json.loads(r)
        for k in ['routes', 'ports', 'urls']:
            if k in d2:
                log('GET %s -> %s = %s' % (p.split('?')[0][-30:], k, json.dumps(d2[k])[:400]))
    except Exception:
        pass

api("DELETE", "/v2/sandboxes/n15b?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
