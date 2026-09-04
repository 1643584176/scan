# -*- coding: utf-8 -*-
"""候选11: v4 ports 暴露面 — 端口暴露 URL 格式/授权/访问验证"""
import json, sys, time, urllib.request
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

api("DELETE", "/v2/sandboxes/n15?teamId=%s&projectId=%s" % (TEAM, PROJ))
time.sleep(2)
c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
           {"projectId": PROJ, "name": "n15", "ports": [8080]}, 60)
log('v4 create ports -> %s | %s' % (c, (r[:600] if r else '').replace(chr(10), ' ')))
if c != 200:
    sys.exit(1)
d = json.loads(r)['sandbox']
sid = d['currentSessionId']
log('sid=%s' % sid)
log('sb keys: %s' % sorted(d.keys()))
time.sleep(4)

# 沙箱内起 HTTP 服务
c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
           {"command": "sh", "args": ["-c", "cd /tmp && echo PORT_TEST_2026 > f.txt && (python3 -m http.server 8080 >/dev/null 2>&1 &) && sleep 1 && curl -s -o /dev/null -w '%%{http_code}' http://127.0.0.1:8080/f.txt"],
            "wait": True, "timeout": 15000}, 30)
log('serve 8080 -> %s | %s' % (c, (r[:300] if r else '').replace(chr(10), ' ')))

# 找端口 URL (GET 沙箱对象)
c, r = api("GET", "/v2/sandboxes/n15?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('GET n15 -> %s' % c)
if c == 200:
    sb = json.loads(r).get('sandbox', {})
    for k in ['ports', 'urls', 'portUrls', 'exposedPorts', 'interactivePort']:
        if k in sb:
            log('  %s = %s' % (k, json.dumps(sb[k])[:300]))
    if 'ports' not in sb:
        log('  keys: %s' % sorted(sb.keys()))

# 尝试常见 URL 格式 (interactive 域 + 端口)
import socket
for hostport in ['sb-1hrzpkdcfi3s.vercel.run', 'sb-1hrzpkdcfi3s.vercel.run:8080']:
    try:
        ip = socket.gethostbyname(hostport.split(':')[0])
        log('DNS %s -> %s' % (hostport, ip))
    except Exception as e:
        log('DNS %s err %s' % (hostport, e))

api("DELETE", "/v2/sandboxes/n15?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
