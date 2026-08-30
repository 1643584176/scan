# -*- coding: utf-8 -*-
"""deep33090: 深挖 host nginx 服务 33090/34121
1) 33090 路径枚举 (login.php/常见路径/方法测试)
2) 34121 TLS 握手拿证书指纹 + HTTPS GET
3) 服务指纹 (Server/技术栈)
输出落盘 + 哨兵 DEEP90_DONE"""
import os, time, socket, ssl, json

OUT = '/vercel/sandbox/deep90.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')

HOST = '88.185.64.100'
P_HTTP = 33090
P_HTTPS = 34121


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def http_req(port, path, method='GET', headers=None, body=None, timeout=5):
    """原始 HTTP 请求"""
    try:
        s = socket.create_connection((HOST, port), timeout=timeout)
        s.settimeout(timeout)
        req = '%s %s HTTP/1.1\r\nHost: %s:%d\r\nConnection: close\r\nUser-Agent: Mozilla/5.0\r\n' % (method, path, HOST, port)
        for k, v in (headers or {}).items():
            req += '%s: %s\r\n' % (k, v)
        req += '\r\n'
        if body:
            req += body
        s.sendall(req.encode())
        data = b''
        try:
            while True:
                chunk = s.recv(8192)
                if not chunk:
                    break
                data += chunk
                if len(data) > 60000:
                    break
        except socket.timeout:
            pass
        s.close()
        return data[:20000]
    except Exception as e:
        return ('ERR %s' % e).encode()[:300]


def https_req(port, path='/', timeout=6):
    """TLS 连接 + GET"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        raw = socket.create_connection((HOST, port), timeout=timeout)
        raw.settimeout(timeout)
        s = ctx.wrap_socket(raw, server_hostname=HOST)
        cert = s.getpeercert()
        s.sendall(b'GET %s HTTP/1.1\r\nHost: %s:%d\r\nConnection: close\r\nUser-Agent: Mozilla/5.0\r\n\r\n' % (path.encode(), HOST.encode(), port))
        data = b''
        try:
            while True:
                chunk = s.recv(8192)
                if not chunk:
                    break
                data += chunk
                if len(data) > 20000:
                    break
        except socket.timeout:
            pass
        s.close()
        return (cert, data[:10000])
    except Exception as e:
        return (None, ('ERR %s' % e).encode()[:300])


def main():
    log('=== DEEP90 PHASE1 33090 HTTP 路径枚举 ===')
    paths = ['/', '/login.php', '/index.php', '/admin', '/admin/', '/api', '/api/',
             '/health', '/healthz', '/status', '/status/', '/metrics', '/debug', '/debug/',
             '/phpmyadmin', '/pma', '/adminer', '/vendor', '/.env', '/config.php',
             '/server-status', '/info.php', '/robots.txt', '/favicon.ico', '/logout',
             '/register', '/forgot', '/users', '/dashboard', '/panel', '/cgi-bin/',
             '/shell', '/backup', '/logs', '/tmp', '/proc', '/wp-login.php']
    for p in paths:
        r = http_req(P_HTTP, p)
        status = r.split(b'\r\n')[0] if r else b''
        log('%s -> %s (len=%d)' % (p, status, len(r)))
        if b'200' in status or b'301' in status or b'302' in status:
            log('  BODY: %s' % r[:800])
        time.sleep(0.15)

    log('=== DEEP90 PHASE2 33090 方法测试 ===')
    for m in ['POST', 'OPTIONS', 'HEAD', 'PUT', 'TRACE']:
        r = http_req(P_HTTP, '/login.php', method=m)
        log('METHOD %s -> %s' % (m, r[:200]))
        time.sleep(0.2)

    log('=== DEEP90 PHASE3 34121 TLS 指纹 ===')
    cert, resp = https_req(P_HTTPS, '/')
    if cert:
        log('cert subject: %s' % cert.get('subject'))
        log('cert issuer: %s' % cert.get('issuer'))
        log('cert SAN: %s' % cert.get('subjectAltName'))
        log('cert notBefore/After: %s %s' % (cert.get('notBefore'), cert.get('notAfter')))
    log('https / -> %s' % resp[:600])
    cert2, resp2 = https_req(P_HTTPS, '/login.php')
    if cert2:
        log('https /login.php -> %s' % resp2[:600])

    log('DEEP90_DONE')
    f.close()


if __name__ == '__main__':
    main()
