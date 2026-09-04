# -*- coding: utf-8 -*-
"""IMDS/metadata 面: custom vs allow-all 模式 169.254.x.x 可达性 + 响应头确认 (不读凭据 body)"""
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

PROBE = '''import socket
T = [('169.254.169.254', 80), ('169.254.169.254', 443), ('169.254.170.2', 80), ('169.254.169.253', 53)]
for ip, port in T:
    s = socket.socket(); s.settimeout(2)
    try:
        rc = s.connect_ex((ip, port))
        print('CONN', ip, port, 'RC', rc, flush=True)
        if rc == 0:
            if port == 53:
                s.close(); continue
            # 只发 HEAD/GET 请求行, 只读响应头
            s.sendall(b'HEAD /latest/meta-data/ HTTP/1.1\\r\\nHost: 169.254.169.254\\r\\n\\r\\n')
            import time; time.sleep(0.5)
            try:
                d = s.recv(1024)
                hdr = d.split(b'\\r\\n')[0] if d else b'EMPTY'
                print('  RESP', hdr.decode(errors='replace'), 'len', len(d), flush=True)
            except Exception as e:
                print('  NORESP', type(e).__name__, flush=True)
    except Exception as e:
        print('CONN', ip, port, 'ERR', type(e).__name__, flush=True)
    finally:
        s.close()
'''

# 1) custom 模式
log('')
log('===== 1) custom-mode IMDS =====')
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM,
           {"projectId": PROJ, "name": "loc15a",
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sida = json.loads(r)["sandbox"]["currentSessionId"]
time.sleep(3)
b64 = base64.b64encode(PROBE.encode()).decode()
c2, out = run_cmd(sida, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log(out[:1500])
api("DELETE", "/v2/sandboxes/loc15a?teamId=%s&projectId=%s" % (TEAM, PROJ))

# 2) allow-all 模式
log('')
log('===== 2) allow-all IMDS =====')
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc15b"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sidb = json.loads(r)["sandbox"]["currentSessionId"]
time.sleep(3)
c2, out = run_cmd(sidb, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log(out[:1500])
api("DELETE", "/v2/sandboxes/loc15b?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
