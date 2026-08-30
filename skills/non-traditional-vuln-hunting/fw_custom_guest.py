# -*- coding: utf-8 -*-
"""D 线: custom 模式 allowedDomains 绕过测试 (在 custom 沙箱内运行)
1) DNS 解析验证: 白名单域 / sslip.io 内部 IP 域 / IP 直连
2) TCP 可达性: 白名单域 / 白名单外域 / IMDS-sslip / VPC-sslip / 网关-sslip
3) HTTP 抓 banner 确认服务身份
"""
import socket, time, json

OUT = '/vercel/sandbox/fwcustom.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def resolve(host):
    try:
        infos = socket.getaddrinfo(host, 80, socket.AF_INET, socket.SOCK_STREAM)
        return sorted(set(i[4][0] for i in infos))
    except Exception as e:
        return 'ERR %s' % e


def tcp(host, port, timeout=5):
    try:
        c = socket.create_connection((host, port), timeout=timeout)
        c.settimeout(4)
        c.sendall(b'GET / HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n' % host.encode())
        d = b''
        try:
            while True:
                ch = c.recv(4096)
                if not ch:
                    break
                d += ch
                if len(d) > 1000:
                    break
        except socket.timeout:
            pass
        c.close()
        return 'OPEN %r' % d[:300]
    except Exception as e:
        return type(e).__name__


def main():
    # 1) DNS 解析对照
    log('--- DNS resolve ---')
    for host in ['httpbin.org', 'example.com', '169.254.169.254.sslip.io',
                 '172.31.0.2.sslip.io', '100.64.0.1.sslip.io',
                 '1.1.1.1.sslip.io', '7f000001.nip.io']:
        log('resolve %s -> %s' % (host, resolve(host)))

    # 2) TCP 可达性 (custom 白名单=httpbin.org)
    log('--- TCP reach ---')
    for host, port in [('httpbin.org', 80), ('httpbin.org', 443),
                       ('example.com', 80), ('example.com', 443),
                       ('169.254.169.254.sslip.io', 80),
                       ('172.31.0.2.sslip.io', 53),
                       ('100.64.0.1.sslip.io', 23456),
                       ('1.1.1.1.sslip.io', 80),
                       ('7f000001.nip.io', 80)]:
        log('tcp %s:%d -> %s' % (host, port, tcp(host, port)))

    # 3) 直接 IP (无域名)
    log('--- raw IP ---')
    for ip, port in [('169.254.169.254', 80), ('172.31.0.2', 53),
                     ('100.64.0.1', 23456), ('8.8.8.8', 53)]:
        log('tcp %s:%d -> %s' % (ip, port, tcp(ip, port)))

    # 4) UDP DNS 白名单行为 (允许域解析)
    log('--- UDP dns ---')
    for host in ['httpbin.org', 'example.com']:
        try:
            ip = socket.gethostbyname(host)
            log('dns %s -> %s' % (host, ip))
        except Exception as e:
            log('dns %s ERR %s' % (host, e))

    log('FWCUSTOM_DONE')
    f.close()


if __name__ == '__main__':
    main()
