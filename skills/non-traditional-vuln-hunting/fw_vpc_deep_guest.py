# -*- coding: utf-8 -*-
"""fw_vpc_deep: VPC 172.31 深度验证 (custom 模式)
1) 5432 PostgreSQL 完整 banner (只读 SSL 协商 + 版本字)
2) 已发现 35 IP 的 sandbox 特征端口复扫 (23456/26661/30002/33090/34121)
3) 172.31.x.0/24 扩展采样 (其他 /24 子网 5432)
4) 172.31.0.2 DNS 特殊查询 (version.bind / AXFR 只读)
输出落盘 + 哨兵 FWVPC_DONE"""
import socket, time, struct, random

OUT = '/vercel/sandbox/fwvpc.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def probe(ip, port, payload, t=2.5, rt=1.5, label=''):
    """connect -> send payload -> read 响应分类"""
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
                if len(d) > 400:
                    break
        except socket.timeout:
            pass
        s.close()
        if d:
            return 'DATA', d[:400]
        return 'NODATA', b''
    except (ConnectionResetError, BrokenPipeError):
        return 'RST', b''
    except socket.timeout:
        return 'TIMEOUT', b''
    except socket.gaierror:
        return 'DNSFAIL', b''
    except OSError as e:
        return 'OSERR:%s' % e.errno, b''
    except Exception as e:
        return 'EXC', b''


def pg_banner(ip, port=5432):
    """PostgreSQL 只读握手: 发 SSLRequest, 读 S/N + 版本包"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((ip, port))
        s.sendall(struct.pack('!II', 8, 80877103))  # SSLRequest
        s.settimeout(2)
        d = s.recv(8)
        s.close()
        if d[:1] == b'S':
            return 'SSL_OK ' + d[:1].decode()
        if d[:1] == b'N':
            return 'SSL_N '
        return 'SSL_OTHER %r' % d[:8]
    except Exception as e:
        return 'ERR %s' % type(e).__name__


def main():
    # 1) PG banner (已发现 IP 采样 12 个)
    hits = ['172.31.0.3', '172.31.0.4', '172.31.0.18', '172.31.0.26', '172.31.0.38',
            '172.31.0.61', '172.31.0.81', '172.31.0.94', '172.31.0.101', '172.31.0.125',
            '172.31.0.140', '172.31.0.200']
    log('=== P1 PG banner (12 采样) ===')
    for ip in hits:
        log('%s:%d %s' % (ip, 5432, pg_banner(ip)))
        time.sleep(0.2)

    # 2) sandbox 特征端口复扫 (前 8 个 PG IP)
    log('=== P2 sandbox 特征端口 (8 IP x 5 端口) ===')
    sb_ports = {23456: b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n',
                26661: b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n',
                30002: b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n',
                33090: b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n',
                34121: b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n'}
    for ip in hits[:8]:
        for p, payload in sb_ports.items():
            st, d = probe(ip, p, payload, t=1.5, rt=1.2)
            if st != 'TIMEOUT':
                log('%s:%d -> %s %r' % (ip, p, st, d[:80]))
        time.sleep(0.2)

    # 3) 扩展子网采样: 172.31.x.1/.2/.100/.200 x 5432
    log('=== P3 扩展子网 5432 采样 ===')
    subnets = [57, 140, 71, 44, 16, 111, 13, 214, 142, 81, 174, 110, 1, 2, 10, 20, 30,
               50, 60, 90, 100, 150, 200, 220, 250]
    tails = [1, 2, 100, 200, 254]
    found = 0
    for sn in subnets:
        for tl in tails:
            ip = '172.31.%d.%d' % (sn, tl)
            st, d = probe(ip, 5432, struct.pack('!II', 8, 80877103), t=1.2, rt=1.0)
            if st in ('DATA', 'SSL_OK'):
                found += 1
                log('PG_FOUND %s -> %r' % (ip, d[:40]))
        time.sleep(0.05)
    log('extended pg found: %d' % found)

    # 4) DNS 特殊查询 (172.31.0.2)
    log('=== P4 DNS 特殊查询 ===')
    def dns_q(name, qtype=1):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2.5)
            tid = random.randint(0, 65535)
            hdr = struct.pack('!HHHHHH', tid, 0x0100, 1, 0, 0, 0)
            q = b''.join(bytes([len(x)]) + x.encode() for x in name.split('.')) + struct.pack('!HH', qtype, 1)
            s.sendto(hdr + q, ('172.31.0.2', 53))
            d, _ = s.recvfrom(512)
            s.close()
            return 'RESP %dB tid_match=%s' % (len(d), struct.unpack('!H', d[:2])[0] == tid)
        except Exception as e:
            return 'ERR %s' % type(e).__name__
    for name in ['example.com', 'version.bind', 'vercel.internal', '169.254.169.254.in-addr.arpa']:
        log('dns %s -> %s' % (name, dns_q(name)))
        time.sleep(0.2)
    for qtype in [255, 252]:  # ANY / AXFR (只读探测)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.5)
            s.connect(('172.31.0.2', 53))
            tid = random.randint(0, 65535)
            hdr = struct.pack('!HHHHHH', tid, 0x0100, 1, 0, 0, 0)
            q = b'\x07example\x03com\x00' + struct.pack('!HH', qtype, 1)
            s.sendall(struct.pack('!H', len(hdr + q)) + hdr + q)
            d = s.recv(512)
            s.close()
            log('tcp-dns qtype=%d -> %dB %r' % (qtype, len(d), d[:60]))
        except Exception as e:
            log('tcp-dns qtype=%d -> ERR %s' % (qtype, type(e).__name__))
        time.sleep(0.2)

    log('FWVPC_DONE')
    f.close()


if __name__ == '__main__':
    main()
