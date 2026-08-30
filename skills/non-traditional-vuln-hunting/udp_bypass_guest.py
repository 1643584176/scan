# -*- coding: utf-8 -*-
"""D 线: deny-all 沙箱全通道测试
1) TCP egress 白名单检查: api.vercel.com / httpbin.org / 8.8.8.8
2) UDP 53 DNS / UDP 自定义
3) ICMP
4) metadata 169.254.169.254 (关键)
5) 网关 100.64.0.1 常用端口 (host 网络栈方向)
6) IPv6 egress
7) 本地 interactive 26661 / 23456
"""
import socket, time, subprocess

OUT = '/vercel/sandbox/udpbypass.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def tcp(host, port, timeout=4):
    try:
        c = socket.create_connection((host, port), timeout=timeout)
        c.close()
        return 'OPEN'
    except Exception as e:
        return type(e).__name__


def udp(host, port, payload, timeout=4):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(payload, (host, port))
        try:
            d, _ = s.recvfrom(512)
            return 'RESP %r' % d[:80]
        except socket.timeout:
            return 'NO_RESP'
    except Exception as e:
        return type(e).__name__
    finally:
        s.close()


def main():
    # 0) 本机 IP
    ip = '127.0.0.1'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('100.64.0.1', 53))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    log('self ip: %s' % ip)

    # 1) TCP egress 白名单
    log('--- TCP egress ---')
    for host, port in [('api.vercel.com', 443), ('vercel.com', 443),
                       ('httpbin.org', 80), ('httpbin.org', 443),
                       ('8.8.8.8', 53), ('1.1.1.1', 80),
                       ('example.com', 80), ('100.64.0.1', 443),
                       ('100.64.0.1', 80), ('100.64.0.1', 23456)]:
        log('tcp %s:%d -> %s' % (host, port, tcp(host, port)))

    # 2) UDP 53 DNS
    log('--- UDP ---')
    log('udp 8.8.8.8:53 A example.com -> %s' % udp('8.8.8.8', 53, b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'))
    log('udp 100.64.0.1:53 A example.com -> %s' % udp('100.64.0.1', 53, b'\x12\x35\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'))
    log('udp 1.1.1.1:53 -> %s' % udp('1.1.1.1', 53, b'\x12\x36\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'))

    # 3) ICMP
    log('--- ICMP ---')
    try:
        r = subprocess.run(['ping', '-c', '1', '-W', '2', '8.8.8.8'],
                           capture_output=True, text=True, timeout=6)
        log('ping 8.8.8.8 rc=%d %s' % (r.returncode, r.stdout.strip()[:120]))
    except Exception as e:
        log('ping EXC %s' % e)
    try:
        r = subprocess.run(['ping', '-c', '1', '-W', '2', '100.64.0.1'],
                           capture_output=True, text=True, timeout=6)
        log('ping 100.64.0.1 rc=%d %s' % (r.returncode, r.stdout.strip()[:120]))
    except Exception as e:
        log('ping gw EXC %s' % e)

    # 4) metadata
    log('--- metadata ---')
    for host in ['169.254.169.254', '100.100.100.200']:
        try:
            c = socket.create_connection((host, 80), timeout=3)
            c.sendall(b'GET /latest/meta-data/ HTTP/1.1\r\nHost: 169.254.169.254\r\nConnection: close\r\n\r\n')
            c.settimeout(3)
            d = b''
            try:
                while True:
                    ch = c.recv(4096)
                    if not ch:
                        break
                    d += ch
                    if len(d) > 1500:
                        break
            except socket.timeout:
                pass
            c.close()
            log('meta %s -> %r' % (host, d[:600]))
        except Exception as e:
            log('meta %s -> %s' % (host, type(e).__name__))

    # 5) 网关 100.64.0.1 全端口扫描关键位 (host 侧网络栈)
    log('--- gw scan ---')
    for p in [22, 53, 80, 443, 23456, 26661, 30001, 30002, 33090, 34121, 8080, 9090]:
        log('gw tcp %d -> %s' % (p, tcp('100.64.0.1', p, 2)))

    # 6) IPv6 egress
    log('--- IPv6 ---')
    try:
        r = subprocess.run(['bash', '-lc', 'cat /proc/net/if_inet6 | head -5; ip -6 route 2>/dev/null | head -5'],
                           capture_output=True, text=True, timeout=6)
        log('ipv6 state: %s | %s' % (r.stdout.strip()[:200], r.stderr.strip()[:100]))
    except Exception as e:
        log('ipv6 EXC %s' % e)

    # 7) 本地服务
    log('--- local ---')
    for p in [23456, 26661, 80, 443, 3000, 8080]:
        log('local tcp %d -> %s' % (p, tcp('127.0.0.1', p, 2)))

    log('UDPBYPASS_DONE')
    f.close()


if __name__ == '__main__':
    main()
