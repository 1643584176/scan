# -*- coding: utf-8 -*-
"""三线: (1) OPEN 端口 banner 区分黑洞/真实服务 (2) PATCH query-projectId 正确调用 (3) v1 无 name 创建对比"""
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

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM,
           {"projectId": PROJ, "name": "loc13",
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc13(custom) sid: %s' % sid)
time.sleep(3)

# 1) banner 探测: 黑洞 vs 真实服务
log('')
log('===== 1) banner probe (blackhole vs real) =====')
SCAN = '''import socket, concurrent.futures
TARGETS = ['172.31.0.2', '172.31.0.3', '10.0.0.2']
PORTS = [22, 80, 443, 5432, 6379, 8080, 8443, 9090, 9200, 27017, 2379, 10250, 6443, 9092, 2181, 8500, 11211, 15672, 5672, 4369, 25672, 3306, 5434, 6432, 6543, 8008, 8081, 8888, 9000, 9100, 9300, 2380, 3000, 5000, 7000, 7001]
def chk(t):
    ip, port = t
    s = socket.socket(); s.settimeout(1.2)
    try:
        rc = s.connect_ex((ip, port))
        if rc != 0:
            return None
        try:
            d = s.recv(256)
            if d:
                return (ip, port, 'DATA', repr(d[:60]))
            return (ip, port, 'NOBANNER', '')
        except Exception as e:
            return (ip, port, 'NORESP', type(e).__name__)
    except Exception as e:
        return None
    finally:
        s.close()
tasks = [(ip, p) for ip in TARGETS for p in PORTS]
with concurrent.futures.ThreadPoolExecutor(50) as ex:
    for res in ex.map(chk, tasks):
        if res:
            print(res[0], res[1], res[2], res[3], flush=True)
'''
b64 = base64.b64encode(SCAN.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 120000)
log('banner: %s' % out[-3000:])

# 2) PATCH 正确调用 (query projectId)
log('')
log('===== 2) PATCH with query projectId =====')
for body in [
    {"networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}},
    {"networkPolicy": {"mode": "deny-all"}},
    {"region": "sfo1"},
    {"runtime": "python3.13"},
]:
    c3, r3 = api("PATCH", "/v2/sandboxes/loc13?teamId=%s&projectId=%s" % (TEAM, PROJ), body)
    log('PATCH %-18s -> %s | %s' % (list(body.keys())[0], c3, r3[:200].replace('\n', ' ')))
    if c3 == 200:
        # GET 确认
        c4, r4 = api("GET", "/v2/sandboxes/loc13?teamId=%s&projectId=%s" % (TEAM, PROJ))
        log('  GET after: %s | %s' % (c4, r4[:200].replace('\n', ' ')))

# 3) v1 创建 (无 name) + networkPolicy 差异
log('')
log('===== 3) v1 create =====')
for body in [
    {"projectId": PROJ},
    {"projectId": PROJ, "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}},
    {"projectId": PROJ, "networkPolicy": {"mode": "deny-all"}},
]:
    c3, r3 = api("POST", "/v1/sandboxes?teamId=%s" % TEAM, body)
    log('POST v1 %s -> %s | %s' % (json.dumps(body)[:70], c3, r3[:250].replace('\n', ' ')))
    if c3 == 200:
        try:
            d = json.loads(r3)
            nm = d.get('sandbox', {}).get('name') or d.get('name')
            log('  v1 name: %s' % nm)
            if nm:
                api("DELETE", "/v1/sandboxes/%s?teamId=%s&projectId=%s" % (nm, TEAM, PROJ))
        except Exception as e:
            log('  parse err %s' % e)
        break

api("DELETE", "/v2/sandboxes/loc13?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
