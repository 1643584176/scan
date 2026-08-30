# -*- coding: utf-8 -*-
"""D 线: custom 模式 VPC payload 探测 (真实服务 vs 中间设备)
1) 172.31.0.0/24 关键端口 payload 指纹 (HTTP/SSH/PG/Redis/MySQL 握手)
2) DNS 特殊查询 172.31.0.2 (version/AXFR/内部域枚举)
3) 响应分类: RST=无服务 / 数据=真实服务 / 挂起=黑洞
"""
import socket, time, struct, random

OUT = '/vercel/sandbox/fwcustom4.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def probe(ip, port, payload, timeout=3, read_timeout=2):
    """连接后发 payload, 收集响应; RST=ConnectionResetError"""
    try:
        c = socket.create_connection((ip, port), timeout=timeout)
        c.settimeout(read_timeout)
        if payload:
            c.sendall(payload)
        d = b''
        try:
            while True:
                ch = c.recv(4096)
                if not ch:
                    break
                d += ch
                if len(d) > 600:
                    break
        except socket.timeout:
            pass
        c.close()
        if d:
            return 'DATA %r' % d[:200]
        return 'CONN-NODATA'
    except ConnectionResetError:
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR %s' % e.errno


def main():
    HTTP = b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n'
    SSH = b'SSH-2.0-probe\r\n'
    PG = struct.pack('!II', 8, 0x04D2162F)
    REDIS = b'PING\r\n'
    MYSQL = b'\x0a\x00\x00\x00\x0a\x35\x2e\x37\x2e\x34\x33\x00'

    # 1) 172.31.0.1-254 关键端口 payload
    log('=== 172.31.0.0/24 payload probe ===')
    ports = {23456: HTTP, 26661: HTTP, 33090: HTTP, 34121: HTTP,
             30001: HTTP, 30002: HTTP, 8080: HTTP, 9090: HTTP,
             80: HTTP, 443: HTTP, 22: SSH, 5432: PG, 6379: REDIS, 3306: MYSQL}
    hits = []
    for i in range(1, 255):
        ip = '172.31.0.%d' % i
        for p, payload in ports.items():
            r = probe(ip, p, payload, 2, 1.5)
            if r not in ('RST', 'TIMEOUT', 'OSERR 113', 'OSERR 111'):
                hits.append((ip, p, r))
                log('HIT %s:%d %s' % (ip, p, r))
        if i % 50 == 0:
            log('progress %d/254, hits=%d' % (i, len(hits)))
    log('total hits: %s' % hits)

    # 2) DNS 特殊查询
    log('=== DNS special 172.31.0.2 ===')
    def dns_q(domain, qtype=1, cls=1):
        tid = random.randint(0, 0xffff)
        hdr = struct.pack('>HHHHHH', tid, 0x0100, 1, 0, 0, 0)
        q = b''.join(bytes([len(p)]) + p.encode() for p in domain.split('.')) + b'\x00'
        q = q + struct.pack('>HH', qtype, cls)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3)
        try:
            s.sendto(hdr + q, ('172.31.0.2', 53))
            d, _ = s.recvfrom(4096)
            rcode = d[3] & 0x0f if len(d) >= 4 else -1
            ancount = struct.unpack('>H', d[6:8])[0] if len(d) >= 8 else -1
            return 'rcode=%d an=%d len=%d' % (rcode, ancount, len(d))
        except socket.timeout:
            return 'TIMEOUT'
        except Exception as e:
            return 'ERR %s' % type(e).__name__
        finally:
            s.close()

    for dom, qt in [('version.bind', 16), ('hostname.bind', 16),
                    ('vercel.internal', 1), ('cell.vercel.internal', 1),
                    ('sandbox.vercel.internal', 1), ('sandboxes.vercel.internal', 1),
                    ('api.vercel.internal', 1), ('celld.vercel.internal', 1),
                    ('ec2.internal', 1), ('compute.internal', 1),
                    ('169.254.169.254', 1), ('metadata.google.internal', 1),
                    ('consul', 1), ('consul.service.consul', 1),
                    ('_dns.resolver.arpa', 12)]:
        log('dns %s qtype=%d -> %s' % (dom, qt, dns_q(dom, qt)))

    # 3) AXFR 尝试
    for zone in ['vercel.internal', 'internal', 'vercel.com']:
        log('axfr %s -> %s' % (zone, dns_q(zone, 252)))

    log('FWCUSTOM4_DONE')
    f.close()


if __name__ == '__main__':
    main()
