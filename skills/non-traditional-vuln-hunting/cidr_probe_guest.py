# -*- coding: utf-8 -*-
"""cidr_probe: custom 模式下放行 CIDR 范围测绘
采样各保留网段随机 IP:随机端口 TCP connect + 已知服务端口
网段: 172.31.0.0/16 (已知放行) / 169.254.0.0/16 (link-local) / 10.0.0.0/8 / 100.64.0.0/10 / 192.168.0.0/16 / 172.16-31
输出落盘 + 哨兵 CIDR_DONE"""
import socket, time, random, struct

OUT = '/vercel/sandbox/cidr.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
random.seed(20260829)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def tcp_probe(ip, port, payload=None, t=2.0, rt=1.0):
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
                if len(d) > 80:
                    break
        except socket.timeout:
            pass
        s.close()
        return 'OPEN DATA=%r' % d[:40] if d else 'OPEN'
    except (ConnectionResetError, BrokenPipeError):
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


def rand_ip_in(net, prefix):
    host_bits = 32 - prefix
    base = net & ((0xFFFFFFFF >> host_bits) << host_bits)
    return base | random.getrandbits(host_bits)


def ip_str(x):
    return '%d.%d.%d.%d' % (x >> 24 & 255, x >> 16 & 255, x >> 8 & 255, x & 255)


pg = struct.pack('!II', 8, 80877103)
log('START')
nets = [
    ('172.31.0.0/16', 0xAC1F0000, 16),
    ('169.254.0.0/16', 0xA9FE0000, 16),
    ('10.0.0.0/8', 0x0A000000, 8),
    ('100.64.0.0/10', 0x64400000, 10),
    ('192.168.0.0/16', 0xC0A80000, 16),
]
# P1 每网段 3 随机 IP x 3 随机端口 (纯 connect)
for name, net, prefix in nets:
    for i in range(3):
        ip = rand_ip_in(net, prefix)
        port = random.choice([22, 80, 443, 3306, 5432, 6379, 8080, 9090, 23456, 33090])
        log('P1 %s rand %s:%d -> %s' % (name, ip_str(ip), port, tcp_probe(ip_str(ip), port)))
# P2 已知服务端口采样
log('--- P2 known ports ---')
for name, net, prefix in nets:
    for i in range(2):
        ip = rand_ip_in(net, prefix)
        log('P2 %s %s:5432 -> %s' % (name, ip_str(ip), tcp_probe(ip_str(ip), 5432, pg)))
        log('P2 %s %s:53 -> %s' % (name, ip_str(ip), tcp_probe(ip_str(ip), 53, b'\x00')))
# P3 对照: 公网 IP
log('--- P3 public ---')
for ip in ['8.8.8.8', '1.1.1.1', '54.172.31.170']:
    log('P3 %s:443 -> %s' % (ip, tcp_probe(ip, 443, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n')))
log('CIDR_DONE')
f.close()
