# -*- coding: utf-8 -*-
"""mmds_probe: custom 模式下 MMDS/IMDS/ECS metadata 可达性 + 内部 DNS 记录
1) 169.254.169.254:80/443/1338 TCP + HTTP GET (Firecracker MMDS / AWS IMDS)
2) 169.254.170.2:80/443 (ECS metadata)
3) 169.254.169.253:53 (R53 Resolver 次地址) + 172.31.0.2:53 对照
4) DNS PTR 169.254.169.254.in-addr.arpa + ec2.internal 子域猜测
输出落盘 + 哨兵 MMDS_DONE"""
import socket, time, struct

OUT = '/vercel/sandbox/mmds.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def tcp_probe(ip, port, payload=None, t=2.5, rt=1.5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        if payload:
            s.sendall(payload)
        s.settimeout(rt)
        d = b''
        try:
            while True:
                ch = s.recv(4096)
                if not ch:
                    break
                d += ch
                if len(d) > 300:
                    break
        except socket.timeout:
            pass
        s.close()
        return 'OPEN DATA=%r' % d[:120] if d else 'OPEN_NODATA'
    except (ConnectionResetError, BrokenPipeError):
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


def dns_q(server, name, qtype=1, t=2.5):
    tid = 0x1234
    hdr = struct.pack('!HHHHHH', tid, 0x0100, 1, 0, 0, 0)
    q = b''.join(struct.pack('B', len(x)) + x.encode() for x in name.split('.')) + b'\x00'
    pkt = hdr + q + struct.pack('!HH', qtype, 1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(t)
        s.sendto(pkt, (server, 53))
        d, _ = s.recvfrom(2048)
        s.close()
        if len(d) < 12:
            return 'SHORT:%d' % len(d)
        rcode = d[3] & 0x0F
        an = struct.unpack('!H', d[6:8])[0]
        return 'rcode=%d an=%d len=%d' % (rcode, an, len(d))
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno


log('START')
GET = b'GET /latest/meta-data/ HTTP/1.1\r\nHost: 169.254.169.254\r\nConnection: close\r\n\r\n'
GETR = b'GET / HTTP/1.1\r\nHost: 169.254.169.254\r\nConnection: close\r\n\r\n'
log('T1 169.254.169.254:80 plain -> %s' % tcp_probe('169.254.169.254', 80))
log('T2 169.254.169.254:80 GET -> %s' % tcp_probe('169.254.169.254', 80, GET))
log('T3 169.254.169.254:443 -> %s' % tcp_probe('169.254.169.254', 443))
log('T4 169.254.169.254:1338 -> %s' % tcp_probe('169.254.169.254', 1338, GETR))
log('T5 169.254.170.2:80 -> %s' % tcp_probe('169.254.170.2', 80, GETR))
log('T6 169.254.170.2:443 -> %s' % tcp_probe('169.254.170.2', 443))
log('T7 169.254.169.253:53 -> %s' % tcp_probe('169.254.169.253', 53, b'\x00'))
log('T8 dns 172.31.0.2 PTR 169.254.169.254.in-addr.arpa -> %s' % dns_q('172.31.0.2', '169.254.169.254.in-addr.arpa', 12))
log('T9 dns 172.31.0.2 A ec2.internal -> %s' % dns_q('172.31.0.2', 'ec2.internal', 1))
log('T10 dns 172.31.0.2 A ip-172-31-0-3.ec2.internal -> %s' % dns_q('172.31.0.2', 'ip-172-31-0-3.ec2.internal', 1))
log('T11 dns 172.31.0.2 A metadata.ec2.internal -> %s' % dns_q('172.31.0.2', 'metadata.ec2.internal', 1))
log('T12 dns 172.31.0.2 A db.vercel.internal -> %s' % dns_q('172.31.0.2', 'db.vercel.internal', 1))
log('T13 dns 169.254.169.253 A example.com -> %s' % dns_q('169.254.169.253', 'example.com', 1))
log('T14 httpbin.org:443 -> %s' % tcp_probe('httpbin.org', 443, b'GET / HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n'))
log('MMDS_DONE')
f.close()
