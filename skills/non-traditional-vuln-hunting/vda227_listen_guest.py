# -*- coding: utf-8 -*-
"""v227 payload (guest): 完整 LISTEN 端口枚举 — tcp6/tcp 所有 LISTEN + 试连
输出到 stdout (cmd wait 捕获)"""
import socket, time

rows6 = []
for ln in open('/proc/net/tcp6').read().splitlines()[1:]:
    p = ln.split()
    if len(p) < 10:
        continue
    if p[3] != '0A':
        continue
    loc = p[1]
    hx, port = loc.rsplit(':', 1)
    port = int(port, 16)
    rows6.append((hx, port, p[7]))

rows4 = []
for ln in open('/proc/net/tcp').read().splitlines()[1:]:
    p = ln.split()
    if len(p) < 10:
        continue
    if p[3] != '0A':
        continue
    loc = p[1]
    hx, port = loc.rsplit(':', 1)
    port = int(port, 16)
    rows4.append((hx, port, p[7]))

print('=== LISTEN tcp6 (%d) ===' % len(rows6), flush=True)
seen = {}
for hx, port, uid in rows6:
    if port in seen:
        continue
    seen[port] = uid
    print('tcp6 :%d uid=%s' % (port, uid), flush=True)
print('=== LISTEN tcp4 (%d) ===' % len(rows4), flush=True)
seen4 = {}
for hx, port, uid in rows4:
    if port in seen4:
        continue
    seen4[port] = uid
    print('tcp4 :%d uid=%s' % (port, uid), flush=True)

# 试连所有唯一端口 (v4 loopback)
print('=== CONNECT test ===', flush=True)
ports = set(seen) | set(seen4)
for port in sorted(ports):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)
        rc = s.connect_ex(('127.0.0.1', port))
        s.close()
        if rc == 0:
            print('OPEN 127.0.0.1:%d' % port, flush=True)
    except Exception as e:
        print('ERR :%d %s' % (port, e), flush=True)

# 非 loopback 网卡 IP
import subprocess
print('=== ips ===', flush=True)
try:
    out = subprocess.check_output(['ip', 'addr'], stderr=subprocess.STDOUT, timeout=5).decode(errors='replace')
    for ln2 in out.splitlines():
        if 'inet ' in ln2:
            print(ln2.strip(), flush=True)
except Exception as e:
    print('ip err %s' % e, flush=True)

print('DONE', flush=True)
