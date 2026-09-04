# -*- coding: utf-8 -*-
"""补测: sfo1 PG 完整结果 + GET /v2/sandboxes/features 功能列表 + enroll 变体"""
import json, sys, time, base64
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s):
    print(s, flush=True)

# 1) features 端点
log('===== features endpoint =====')
for path in [
    "/v2/sandboxes/features?teamId=%s&projectId=%s" % (TEAM, PROJ),
    "/v2/sandboxes/features?projectId=%s" % PROJ,
]:
    c, r = api("GET", path)
    log('%s -> %s | %s' % (path.split('?')[0], c, r[:500].replace('\n', ' ')))

# 2) enroll 变体
log('')
log('===== enroll variants =====')
for body in [
    {"projectId": PROJ, "teamId": TEAM},
    {"projectId": PROJ},
    {"feature": "drives", "projectId": PROJ},
]:
    c, r = api("POST", "/v2/sandboxes/drives/enroll", body)
    log('POST enroll %s -> %s | %s' % (json.dumps(body)[:80], c, r[:300].replace('\n', ' ')))

# 3) sfo1 PG 完整复测
log('')
log('===== sfo1 PG repro =====')
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM,
           {"projectId": PROJ, "name": "sfod1b", "region": "sfo1",
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
log('create: %s' % c)
if c == 200:
    sid = json.loads(r)["sandbox"]["currentSessionId"]
    time.sleep(3)
    PG = '''import socket,struct,time
for ip in ['172.31.0.2','172.31.0.3','10.0.0.2']:
    s=socket.socket(); s.settimeout(4)
    rc=s.connect_ex((ip,5432))
    print(ip, 'RC', rc, end=' ')
    if rc==0:
        s.sendall(struct.pack('!II',8,80877103)); time.sleep(0.8)
        try: print('RESP', s.recv(4))
        except Exception as e: print('ERR', type(e).__name__)
    else: print()
'''
    b64 = base64.b64encode(PG.encode()).decode()
    sc = 'echo %s | base64 -d | python3' % b64
    c2, r2 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c", sc], "wait": True, "logs": True, "timeout": 40000})
    log('cmd: %s' % c2)
    # 提取 data 字段
    out = ''
    for line in r2.splitlines():
        if '"data"' in line:
            try: out += json.loads(line).get('data', '')
            except Exception: pass
    log('PG-OUT>>>')
    log(out[:600])
    log('<<<END')
    api("DELETE", "/v2/sandboxes/sfod1b?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
