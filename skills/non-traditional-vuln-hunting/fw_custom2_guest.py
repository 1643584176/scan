# -*- coding: utf-8 -*-
"""D 线: custom 模式 VPC 探测 (172.31.0.0/24 + 周边)
1) httpbin.org 重试 (curl + UA) 确认白名单连通性
2) 172.31.0.0/24 常见端口 TCP 扫描 (VPC!)
3) 172.31.0.2 详细指纹 (53/80/443/8080)
4) 其他子网网关 (172.31.16.1 / 172.31.32.1 / 172.31.64.1)
5) UDP 53 到 172.31.0.2 (DNS over custom)
"""
import socket, time, subprocess

OUT = '/vercel/sandbox/fwcustom2.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def tcp(host, port, timeout=3, banner=True):
    try:
        c = socket.create_connection((host, port), timeout=timeout)
        if banner:
            c.settimeout(2)
            c.sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
            d = b''
            try:
                while True:
                    ch = c.recv(4096)
                    if not ch:
                        break
                    d += ch
                    if len(d) > 400:
                        break
            except socket.timeout:
                pass
        c.close()
        return 'OPEN %r' % d[:200] if banner else 'OPEN'
    except Exception as e:
        return type(e).__name__


def main():
    # 1) httpbin 重试
    log('--- httpbin retry ---')
    try:
        r = subprocess.run(['curl', '-sv', '-m', '8', 'http://httpbin.org/get'],
                           capture_output=True, text=True, timeout=12)
        log('curl httpbin rc=%d\n%s\n%s' % (r.returncode, r.stdout[:400], r.stderr[-400:]))
    except Exception as e:
        log('curl EXC %s' % e)
    log('tcp httpbin.org:443 retry -> %s' % tcp('httpbin.org', 443, 5))

    # 2) 172.31.0.0/24 关键端口扫描
    log('--- 172.31.0.0/24 scan ---')
    ports = [22, 53, 80, 443, 3306, 5432, 6379, 8080, 9090, 23456, 26661, 30001, 30002]
    hits = []
    for i in range(1, 255):
        ip = '172.31.0.%d' % i
        for p in ports:
            r = tcp(ip, p, 1.2, banner=False)
            if r == 'OPEN':
                hits.append((ip, p))
                log('HIT %s:%d' % (ip, p))
    log('scan hits: %s' % hits)

    # 3) 172.31.0.2 详细指纹
    log('--- 172.31.0.2 detail ---')
    for p in [53, 80, 443, 8080, 22]:
        log('172.31.0.2:%d -> %s' % (p, tcp('172.31.0.2', p, 3)))

    # 4) 其他子网
    log('--- other subnets ---')
    for ip in ['172.31.16.1', '172.31.32.1', '172.31.64.1', '172.31.0.1', '172.31.255.254']:
        for p in [53, 80, 443, 22]:
            r = tcp(ip, p, 1.5, banner=False)
            if r == 'OPEN':
                log('HIT %s:%d' % (ip, p))

    # 5) UDP 53
    log('--- UDP 53 ---')
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(4)
    try:
        s.sendto(b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01', ('172.31.0.2', 53))
        d, _ = s.recvfrom(512)
        log('udp 172.31.0.2:53 example.com -> %r' % d[:60])
    except Exception as e:
        log('udp 172.31.0.2:53 -> %s' % type(e).__name__)
    finally:
        s.close()

    log('FWCUSTOM2_DONE')
    f.close()


if __name__ == '__main__':
    main()
