# -*- coding: utf-8 -*-
"""跟进: (1) fs/write application/gzip 写原语矩阵 (2) sandbox-init 二进制字符串扫描 (3) internal.vercel.com 解析"""
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

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc5"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc5 sid: %s' % sid)
time.sleep(3)

# 1) fs/write gzip 变体
log('')
log('===== 1) fs/write gzip variants =====')
PW = "/v2/sandboxes/sessions/%s/fs/write?teamId=%s" % (sid, TEAM)
variants = [
    ('json-path-content', gzip.compress(json.dumps({"path": "/vercel/sandbox/gz1.txt", "content": base64.b64encode(b'hello').decode()}).encode())),
    ('json-path-data', gzip.compress(json.dumps({"path": "/vercel/sandbox/gz2.txt", "data": base64.b64encode(b'hello').decode()}).encode())),
    ('json-path-text', gzip.compress(json.dumps({"path": "/vercel/sandbox/gz3.txt", "text": "hello"}).encode())),
    ('json-path', gzip.compress(json.dumps({"path": "/vercel/sandbox/gz4.txt"}).encode())),
    ('plain-text', gzip.compress(b'hello world')),
    ('empty-gzip', gzip.compress(b'')),
    ('raw-gzip-hello', gzip.compress(b'hello')),
]
for name, raw in variants:
    c3, r3 = api_ct('POST', PW, raw=raw, ct='application/gzip')
    log('fs/write %-16s -> %s | %s' % (name, c3, r3[:300].replace('\n', ' ')))

# 2) 若第一步有任何 200, 验证文件
log('')
log('===== 2) verify write =====')
c2, out = run_cmd(sid, 'sh', ['-c', 'ls -la /vercel/sandbox/ 2>/dev/null; echo ===; for f in /vercel/sandbox/gz*.txt; do [ -f "$f" ] && echo "$f: $(cat $f 2>/dev/null)"; done; echo ===; find / -name "gz*.txt" -not -path "/proc/*" 2>/dev/null | head -10'], 30000)
log(out[:1500])

# 3) sandbox-init 二进制字符串扫描
log('')
log('===== 3) sandbox-init strings (python) =====')
ST = '''import re
data = open('/run/vercel/share/sandbox-init','rb').read()
print('size', len(data))
seen = set()
for m in re.finditer(rb'[\\x20-\\x7e]{6,}', data):
    s = m.group().decode(errors='replace')
    low = s.lower()
    if any(k in low for k in ['http', 'vercel', '.com', '.io', '.net', 'token', 'secret', 'key', 'auth', '/api', '/v1', '/v2', 'internal', '.sock', 'ws://', 'wss://']):
        if s not in seen:
            seen.add(s)
            print(s[:160])
'''
b64 = base64.b64encode(ST.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log(out[-4000:])

# 4) internal.vercel.com 解析 (控制面侧 DNS 对比用, 本机 nslookup 走系统 DNS)
log('')
log('===== 4) internal.vercel.com =====')
import subprocess
try:
    r = subprocess.run(['nslookup', 'internal.vercel.com'], capture_output=True, timeout=20, text=True)
    log(r.stdout[-600:])
except Exception as e:
    log('nslookup err: %s' % e)

api("DELETE", "/v2/sandboxes/loc5?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
