# -*- coding: utf-8 -*-
"""vpc_probe: 172.31.0.0/24 VPC 内网探测 (J500 遗留缺口)
1) TCP 快速扫描 172.31.0.1-254 关键端口 (80/443/53/22/2375/6443/8080/9090/42664/10250)
2) ARP/邻居表
3) 对开放端口 HTTP banner
4) 172.31.0.2:53 特殊查询 (version.bind CHAOS / HTTPS SRV / 枚举)
5) 169.254.169.254 对照 (已知隔离)
输出落盘 + 哨兵 VPCPROBE_DONE"""
import socket, time, os, sys, struct, subprocess, random, select

OUT = '/vercel/sandbox/vpcprobe.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


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
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + r.stderr).strip()[:600]
    except Exception as e:
        return 'ERR %s' % e


def tcp_probe(ip, port, t=0.8):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        r = s.connect_ex((ip, port))
        s.close()
        return r
    except Exception as e:
        return -1


def batch_scan(ips, ports, t=0.6):
    """非阻塞批量扫描, 返回 [(ip, port), ...]"""
    socks = {}
    for ip in ips:
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setblocking(False)
                err = s.connect_ex((ip, port))
                if err in (0, 10035, 115):  # 0=即时成功, WSAEWOULDBLOCK/115=EINPROGRESS
                    socks[(ip, port)] = s
                else:
                    s.close()
            except Exception:
                pass
    hits = []
    deadline = time.time() + t + 1
    while socks and time.time() < deadline:
        rlist, _, _ = select.select(list(socks.values()), [], [], 0.3)
        for s in rlist:
            ip, port = [k for k, v in socks.items() if v is s][0]
            try:
                err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if err == 0:
                    hits.append((ip, port))
            except Exception:
                pass
            s.close()
            del socks[(ip, port)]
    for s in socks.values():
        try:
            s.close()
        except Exception:
            pass
    return hits


def dns_query_raw(domain, qtype=1, server='172.31.0.2', t=4):
    """构造 DNS 查询发往指定服务器"""
    tid = random.randint(0, 0xffff)
    hdr = struct.pack('>HHHHHH', tid, 0x0100, 1, 0, 0, 0)
    q = b''.join(bytes([len(p)]) + p.encode() for p in domain.split('.')) + b'\x00'
    qtype_b = struct.pack('>HH', qtype, 1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(t)
        s.sendto(hdr + q + qtype_b, (server, 53))
        data, _ = s.recvfrom(4096)
        s.close()
        if len(data) >= 12:
            rcode = data[3] & 0x0f
            ancount = struct.unpack('>H', data[6:8])[0]
            return 'rcode=%d ancount=%d len=%d' % (rcode, ancount, len(data))
        return 'short %dB' % len(data)
    except socket.timeout:
        return 'TIMEOUT'
    except Exception as e:
        return 'ERR %s' % e


log('=== PHASE1 TCP 扫描 172.31.0.0/24 ===')
ips = ['172.31.0.%d' % i for i in range(1, 255)]
ports = [53, 80, 443, 22, 2375, 6443, 8080, 9090, 42664, 10250]
hits = []
# 分 4 批避免 select 超限
for batch in range(4):
    sub = ips[batch * 64:(batch + 1) * 64]
    r = batch_scan(sub, ports, t=0.7)
    for ip, port in r:
        log('OPEN %s:%d' % (ip, port))
        hits.append((ip, port))
    log('batch%d done, cumulative hits=%d' % (batch, len(hits)))
    time.sleep(1)
log('total hits: %d' % len(hits))

log('=== PHASE2 ARP/邻居表 ===')
log('ip neigh: %s' % sh('ip neigh 2>/dev/null | head -20'))
log('arp -a: %s' % sh('arp -a 2>/dev/null | head -20'))

log('=== PHASE3 HTTP banner (开放端口) ===')
for ip, port in hits[:20]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, port))
        req = b'GET / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n' % ip.encode()
        s.sendall(req)
        data = b''
        while True:
            try:
                c = s.recv(2048)
            except socket.timeout:
                break
            if not c:
                break
            data += c
            if len(data) > 2000:
                break
        s.close()
        log('banner %s:%d -> %s' % (ip, port, data[:300].replace(b'\r', b'').replace(b'\n', b' ')[:300]))
    except Exception as e:
        log('banner %s:%d ERR %s' % (ip, port, e))

log('=== PHASE4 DNS 特殊查询 172.31.0.2 ===')
for dom, qt in [('version.bind', 16), ('hostname.bind', 16), ('vercel.internal', 1),
                ('_https._tcp.vercel.internal', 65), ('metadata.vercel.internal', 1),
                ('ec2.internal', 1), ('169.254.169.254', 1)]:
    log('DNS %s qtype=%d -> %s' % (dom, qt, dns_query_raw(dom, qt, '172.31.0.2')))

log('=== PHASE5 IMDS 对照 ===')
for ip in ['169.254.169.254', '169.254.170.2']:
    log('TCP %s:80 -> %s' % (ip, tcp_probe(ip, 80, 1.5)))
    log('TCP %s:443 -> %s' % (ip, tcp_probe(ip, 443, 1.5)))

log('VPCPROBE_DONE')
f.close()
