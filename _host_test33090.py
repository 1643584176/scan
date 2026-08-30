# -*- coding: utf-8 -*-
"""本地机器测试 88.185.64.100:33090/34121 是否公网可达
区分: 公网暴露(非漏洞) vs Vercel 内网(漏洞证据)"""
import socket, sys, ssl

sys.stdout.reconfigure(encoding='utf-8')

IP = '88.185.64.100'


def probe(ip, port, timeout=5):
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
        data = b''
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 2000:
                    break
        except socket.timeout:
            pass
        s.close()
        return data[:2000]
    except Exception as e:
        return ('ERR %s' % e).encode()[:200]


def tls_probe(ip, port, timeout=5):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        raw = socket.create_connection((ip, port), timeout=timeout)
        s = ctx.wrap_socket(raw, server_hostname=ip)
        s.settimeout(timeout)
        s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
        data = b''
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 2000:
                    break
        except socket.timeout:
            pass
        s.close()
        return data[:2000]
    except Exception as e:
        return ('ERR %s' % e).encode()[:200]


print('=== 本地机器公网测试 88.185.64.100 ===')
r = probe(IP, 33090)
print('HTTP 33090:', r)
r = tls_probe(IP, 34121)
print('TLS 34121:', r)
r = probe(IP, 23456)
print('HTTP 23456:', r)
# PTR
for q in [IP, '151.36.64.100', '100.64.185.88', '100.64.36.151']:
    try:
        print('PTR', q, '->', socket.gethostbyaddr(q)[0])
    except Exception as e:
        print('PTR', q, 'ERR', e)
print('=== DONE ===')
