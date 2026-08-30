# -*- coding: utf-8 -*-
"""T 线: 连接复用 + 明文 HTTP 注入验证"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/tinj1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('tinj1 sid:', sid, flush=True)

# node 脚本: 同一 TLS 连接发两个 HTTP/1.1 请求 (Host 不同)
NODE1 = r'''
const tls = require('tls');
const net = require('net');
const socket = net.connect(443, 'httpbin.org');
const t = tls.connect({socket, servername: 'httpbin.org', rejectUnauthorized: false});
let buf = '';
t.on('data', d => { buf += d.toString(); if (buf.includes('SECOND_RESP')) { console.log(buf.slice(0, 1500)); process.exit(0); } });
t.on('connect', () => {
  t.write('GET /anything HTTP/1.1\r\nHost: httpbin.org\r\nConnection: keep-alive\r\n\r\n');
  setTimeout(() => {
    t.write('GET /anything HTTP/1.1\r\nHost: 1.1.1.1\r\nConnection: close\r\nX-Second: 1\r\n\r\n');
  }, 500);
});
setTimeout(() => { console.log('TIMEOUT ' + buf.slice(0, 800)); process.exit(1); }, 15000);
'''
b64 = __import__('base64').b64encode(NODE1.encode()).decode()
inj = "import base64;open('/vercel/sandbox/keepalive.js','wb').write(base64.b64decode('%s'))" % b64
c, r = cmd(sid, 'node', ['-e', inj], timeout_ms=30000)
print('inject node:', c, flush=True)
time.sleep(1)
c, r = cmd(sid, 'node', ['/vercel/sandbox/keepalive.js'], timeout_ms=40000)
print('=== keepalive ->', c, flush=True)
for line in r.splitlines():
    if '"data"' in line:
        try:
            print(json.loads(line).get('data', '')[:1500], flush=True)
        except Exception:
            pass
time.sleep(1)

# 明文 HTTP: Host=httpbin.org 但连接 1.1.1.1:80 (注入按 Host?)
tests = [
    ('plain-Host-httpbin-to-1111', 'curl -s --max-time 8 http://1.1.1.1/ -H "Host: httpbin.org" 2>&1 | head -15'),
    ('plain-Host-httpbin-to-80', 'curl -s --max-time 8 http://httpbin.org/anything -H "Host: httpbin.org" 2>&1 | head -20'),
    ('tls-Host-evil-port443', 'curl -sk --max-time 8 https://httpbin.org/anything -H "Host: evil.invalid" 2>&1 | head -20'),
]
for tag, script in tests:
    c, r = cmd(sid, 'sh', ['-c', script], timeout_ms=30000)
    print('=== %s -> %d' % (tag, c), flush=True)
    for line in r.splitlines():
        if '"data"' in line:
            try:
                print(json.loads(line).get('data', '')[:600], flush=True)
            except Exception:
                pass
    time.sleep(1)

print('=== T-REUSE DONE ===', flush=True)
