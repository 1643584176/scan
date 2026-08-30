# -*- coding: utf-8 -*-
"""D 线: custom 模式决定性验证
1) UDP DNS 172.31.0.2 源地址打印 (直连 vs NAT)
2) TCP DNS over 172.31.0.2:53 (标准 DNS-over-TCP)
3) httpbin.org 精细: curl -k https + SNI + 各 IP 直连 443
4) 172.31.0.2 高端口行为 (RST=中间设备 / timeout=黑洞)
5) 172.31.0.0/16 随机 IP 随机端口行为采样
"""
import socket, time, struct, random, subprocess

OUT = '/vercel/sandbox/fwcustom3.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def udp_dns(server, domain='example.com', t=4):
    tid = random.randint(0, 0xffff)
    hdr = struct.pack('>HHHHHH', tid, 0x0100, 1, 0, 0, 0)
    q = b''.join(bytes([len(p)]) + p.encode() for p in domain.split('.')) + b'\x00'
    q = q + struct.pack('>HH', 1, 1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(t)
    try:
        s.sendto(hdr + q, (server, 53))
        data, src = s.recvfrom(4096)
        rcode = data[3] & 0x0f if len(data) >= 4 else -1
        return 'SRC=%s rcode=%d len=%d' % (src[0], rcode, len(data))
    except socket.timeout:
        return 'TIMEOUT'
    except Exception as e:
        return 'ERR %s' % e
    finally:
        s.close()


def tcp_dns(server, domain='example.com', t=4):
    """DNS over TCP: 2 字节长度前缀 + 查询"""
    tid = random.randint(0, 0xffff)
    hdr = struct.pack('>HHHHHH', tid, 0x0100, 1, 0, 0, 0)
    q = b''.join(bytes([len(p)]) + p.encode() for p in domain.split('.')) + b'\x00'
    q = q + struct.pack('>HH', 1, 1)
    msg = hdr + q
    try:
        c = socket.create_connection((server, 53), timeout=t)
        c.settimeout(t)
        c.sendall(struct.pack('>H', len(msg)) + msg)
        ln = c.recv(2)
        if len(ln) != 2:
            c.close()
            return 'short-len %r' % ln
        resp = c.recv(struct.unpack('>H', ln)[0])
        c.close()
        rcode = resp[3] & 0x0f if len(resp) >= 4 else -1
        return 'TCP-DNS rcode=%d len=%d' % (rcode, len(resp))
    except Exception as e:
        return 'EXC %s' % type(e).__name__


def tcp_conn(ip, port, t=3):
    try:
        c = socket.create_connection((ip, port), timeout=t)
        c.close()
        return 'OPEN'
    except Exception as e:
        return type(e).__name__


def main():
    log('=== 1) UDP DNS src ===')
    for server in ['172.31.0.2', '172.31.0.1', '8.8.8.8']:
        log('udp-dns %s -> %s' % (server, udp_dns(server)))

    log('=== 2) TCP DNS over 172.31.0.2 ===')
    log('tcp-dns 172.31.0.2 example.com -> %s' % tcp_dns('172.31.0.2'))

    log('=== 3) httpbin fine ===')
    try:
        r = subprocess.run(['curl', '-sk', '-m', '10', 'https://httpbin.org/get'],
                           capture_output=True, text=True, timeout=14)
        log('curl https httpbin rc=%d out=%s err=%s' % (r.returncode, r.stdout[:150].replace('\n', ' '), r.stderr[-200:].replace('\n', ' ')))
    except Exception as e:
        log('curl https EXC %s' % e)
    for ip in ['34.202.68.214', '3.234.68.252', '54.172.31.170']:
        log('direct %s:443 -> %s' % (ip, tcp_conn(ip, 443)))

    log('=== 4) 172.31.0.2 high ports ===')
    for p in [22, 80, 443, 3306, 5432, 6379, 8080, 9090, 23456, 26661, 30001, 30002, 33090, 34121, 50000, 60000]:
        log('172.31.0.2:%d -> %s' % (p, tcp_conn('172.31.0.2', p, 2)))

    log('=== 5) random samples 172.31.x ===')
    random.seed(42)
    for _ in range(12):
        ip = '172.31.%d.%d' % (random.randint(0, 255), random.randint(1, 254))
        p = random.choice([22, 80, 443, 3306, 5432, 6379, 8080, 9090, 23456, 26661, 30001, 30002])
        log('rand %s:%d -> %s' % (ip, p, tcp_conn(ip, p, 1.5)))

    log('FWCUSTOM3_DONE')
    f.close()


if __name__ == '__main__':
    main()
