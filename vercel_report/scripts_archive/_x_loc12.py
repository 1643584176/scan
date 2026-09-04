# -*- coding: utf-8 -*-
"""两线: (1) custom 策略上下文 VPC 端口全扫 (D 线机制延伸) (2) PATCH 字段变体 + v1 旧版 API 对比"""
import json, sys, time, base64
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s):
    print(s, flush=True)

def run_cmd(sid, command, args, timeout_ms=30000):
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
               {"command": command, "args": args, "wait": True, "logs": True, "timeout": timeout_ms})
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try: out += json.loads(line).get('data', '')
            except Exception: pass
    return c, out

# custom 策略沙箱 (D 线上下文)
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM,
           {"projectId": PROJ, "name": "loc12",
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc12(custom) sid: %s' % sid)
time.sleep(3)

# 1) custom 上下文 VPC 端口全扫
log('')
log('===== 1) custom-mode VPC port scan =====')
SCAN = '''import socket, concurrent.futures
TARGETS = ['172.31.0.2', '172.31.0.3', '10.0.0.2', '172.31.0.1']
PORTS = [22, 53, 80, 443, 3306, 5432, 5433, 5434, 5435, 5436, 5437, 5438, 5439, 6432, 6543, 6379, 8008, 8080, 8081, 8443, 8888, 9000, 9090, 9100, 9200, 9300, 2375, 2376, 2379, 2380, 27017, 28017, 11211, 15672, 5672, 4369, 25672, 10250, 6443, 9092, 2181, 8500, 8300, 8600, 4646, 4647, 3000, 5000, 7000, 7001, 25060, 25061, 8086, 8087, 9419, 4444, 7002, 4369]
def chk(t):
    ip, port = t
    s = socket.socket(); s.settimeout(1.5)
    try:
        rc = s.connect_ex((ip, port))
        if rc == 0:
            return (ip, port)
    except Exception:
        pass
    finally:
        s.close()
    return None
tasks = [(ip, p) for ip in TARGETS for p in PORTS]
opens = []
with concurrent.futures.ThreadPoolExecutor(50) as ex:
    for res in ex.map(chk, tasks):
        if res:
            opens.append(res)
            print(res[0], res[1], flush=True)
print('TOTAL', len(opens), flush=True)
'''
b64 = base64.b64encode(SCAN.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 150000)
log('scan: %s' % out[-3000:])

# 2) PATCH 字段变体
log('')
log('===== 2) PATCH variants =====')
for body in [
    {"projectId": PROJ, "networkPolicy": {"mode": "deny-all"}},
    {"projectId": PROJ, "networkPolicy": {"mode": "custom", "allowedDomains": ["example.com"]}},
    {"projectId": PROJ, "region": "sfo1"},
    {"projectId": PROJ, "runtime": "python3.13"},
    {"projectId": PROJ, "env": {"FOO": "bar"}},
    {"projectId": PROJ, "status": "stopped"},
]:
    c3, r3 = api("PATCH", "/v2/sandboxes/loc12?teamId=%s" % TEAM, body)
    log('PATCH %s -> %s | %s' % (list(body.keys())[1] if len(body) > 1 else list(body.keys())[0], c3, r3[:150].replace('\n', ' ')))

# 3) v1 旧版 API 对比
log('')
log('===== 3) v1 API compare =====')
c3, r3 = api("POST", "/v1/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc12v1"})
log('POST /v1/sandboxes -> %s | %s' % (c3, r3[:250].replace('\n', ' ')))
if c3 == 200:
    try:
        sid1 = json.loads(r3).get('sandbox', {}).get('currentSessionId') or json.loads(r3).get('session', {}).get('id')
        log('v1 sid: %s' % sid1)
        if sid1:
            c3, r3 = api("POST", "/v1/sandboxes/sessions/%s/cmd?teamId=%s" % (sid1, TEAM),
                         {"command": "echo", "args": ["v1-ok"], "wait": True, "logs": True, "timeout": 10000})
            log('v1 cmd -> %s | %s' % (c3, r3[:150].replace('\n', ' ')))
            c3, r3 = api("POST", "/v1/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid1, TEAM),
                         {"mode": "deny-all"})
            log('v1 policy -> %s | %s' % (c3, r3[:150].replace('\n', ' ')))
        api("DELETE", "/v1/sandboxes/loc12v1?teamId=%s&projectId=%s" % (TEAM, PROJ))
    except Exception as e:
        log('v1 parse err: %s' % e)

api("DELETE", "/v2/sandboxes/loc12?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
