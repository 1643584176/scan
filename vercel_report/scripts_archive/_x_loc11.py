# -*- coding: utf-8 -*-
"""两线: (1) VPC 内网主机端口指纹 (PG 主机其它服务?) (2) 控制面剩余端点 (PATCH/快照/版本前缀/跨沙箱 sid)"""
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

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc11"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc11 sid: %s' % sid)
time.sleep(3)

# 1) VPC 内网主机端口指纹
log('')
log('===== 1) VPC host port fingerprint =====')
SCAN = '''import socket, concurrent.futures
TARGETS = ['172.31.0.2', '172.31.0.3', '10.0.0.2', '172.31.57.1', '192.168.0.2']
PORTS = [22, 53, 80, 443, 5432, 5433, 5434, 5435, 5436, 5437, 5438, 5439, 6432, 6543, 6379, 8008, 8080, 8081, 8443, 8888, 9000, 9090, 9100, 9200, 9300, 2375, 2376, 2379, 2380, 27017, 28017, 11211, 15672, 5672, 4369, 25672, 10250, 6443, 9092, 2181, 8500, 8300, 8600, 4646, 4647, 3000, 5000, 7000, 7001]
def chk(t):
    ip, port = t
    s = socket.socket(); s.settimeout(1.2)
    try:
        rc = s.connect_ex((ip, port))
        if rc == 0:
            return (ip, port, 'OPEN')
    except Exception:
        pass
    finally:
        s.close()
    return None
tasks = [(ip, p) for ip in TARGETS for p in PORTS]
with concurrent.futures.ThreadPoolExecutor(40) as ex:
    for res in ex.map(chk, tasks):
        if res:
            print(res[0], res[1], res[2], flush=True)
'''
b64 = base64.b64encode(SCAN.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 120000)
log('scan: %s' % out[-2500:])

# 2) 控制面剩余端点
log('')
log('===== 2) control-plane leftovers =====')
# PATCH 沙箱
for body in [
    {"name": "loc11r"},
    {"networkPolicy": {"mode": "deny-all"}},
    {"region": "sfo1"},
]:
    c3, r3 = api("PATCH", "/v2/sandboxes/loc11?teamId=%s" % TEAM, body)
    log('PATCH %s -> %s | %s' % (list(body.keys())[0], c3, r3[:150].replace('\n', ' ')))
# 手动快照
c3, r3 = api("POST", "/v2/sandboxes/snapshots?teamId=%s" % TEAM, {"sourceSessionId": sid})
log('POST snapshots -> %s | %s' % (c3, r3[:200].replace('\n', ' ')))
c3, r3 = api("POST", "/v2/sandboxes/snapshots?teamId=%s" % TEAM, {"sessionId": sid, "name": "manual1"})
log('POST snapshots2 -> %s | %s' % (c3, r3[:200].replace('\n', ' ')))
# 版本前缀
for v in ['v1', 'v3', 'v4', 'v10']:
    c3, r3 = api("GET", "/%s/sandboxes?teamId=%s&project=%s&limit=1" % (v, TEAM, PROJ))
    log('GET /%s/sandboxes -> %s | %s' % (v, c3, r3[:120].replace('\n', ' ')))
# 跨沙箱 sid (另一个沙箱的 sid 在本沙箱上下文调用)
c3, r3 = api("POST", "/v2/sandboxes/sessions/sbx_tDcBPxp68UFF7xFWNo4hM3WGIwiG/cmd?teamId=%s" % TEAM,
             {"command": "echo", "args": ["hi"], "wait": True, "logs": True, "timeout": 10000})
log('cross-sandbox sid cmd -> %s | %s' % (c3, r3[:200].replace('\n', ' ')))
# DELETE 坏 projectId
c3, r3 = api("DELETE", "/v2/sandboxes/nonexist?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DELETE nonexist -> %s | %s' % (c3, r3[:150].replace('\n', ' ')))

api("DELETE", "/v2/sandboxes/loc11?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
