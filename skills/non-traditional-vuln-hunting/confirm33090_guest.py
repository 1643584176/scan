# -*- coding: utf-8 -*-
"""confirm33090: 确认 host 33090/34121 Freebox 服务归属与边界
1) PTR 反查 88.185.64.100 (归属判断)
2) Freebox 登录页完整抓取 (设备识别, 只读)
3) Freebox API 只读探测 (/api/v1/ 未认证响应)
4) 33090 邻接端口抽查 (33080-33100)
输出落盘 + 哨兵 CFM90_DONE"""
import os, time, socket, ssl

OUT = '/vercel/sandbox/cfm90.out'
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


def http_req(port, path, method='GET', headers=None, timeout=5):
    try:
        s = socket.create_connection((HOST, port), timeout=timeout)
        s.settimeout(timeout)
        req = '%s %s HTTP/1.1\r\nHost: %s:%d\r\nConnection: close\r\nUser-Agent: Mozilla/5.0\r\n' % (method, path, HOST, port)
        for k, v in (headers or {}).items():
            req += '%s: %s\r\n' % (k, v)
        req += '\r\n'
        s.sendall(req.encode())
        data = b''
        try:
            while True:
                chunk = s.recv(8192)
                if not chunk:
                    break
                data += chunk
                if len(data) > 30000:
                    break
        except socket.timeout:
            pass
        s.close()
        return data[:12000]
    except Exception as e:
        return ('ERR %s' % e).encode()[:200]


def main():
    log('=== CFM90 PHASE1 PTR 反查 ===')
    for q in [HOST, '88.185.64.1', '88.185.0.1']:
        try:
            name = socket.gethostbyaddr(q)
            log('PTR %s -> %s' % (q, name[0]))
        except Exception as e:
            log('PTR %s ERR %s' % (q, e))

    log('=== CFM90 PHASE2 Freebox 登录页完整抓取 ===')
    r = http_req(P_HTTP, '/login.php')
    log('login.php len=%d' % len(r))
    log('PAGE: %s' % r[:6000])

    log('=== CFM90 PHASE3 Freebox API 只读探测 ===')
    for p in ['/api/v1/', '/api/v1/login', '/api/v1/version', '/api/v1/system',
              '/api/v1/connection', '/api/version', '/login', '/index.html', '/resources/']:
        r = http_req(P_HTTP, p)
        status = r.split(b'\r\n')[0] if r else b''
        log('%s -> %s (len=%d)' % (p, status, len(r)))
        time.sleep(0.2)

    log('=== CFM90 PHASE4 邻接端口抽查 ===')
    import select
    pend = []
    for port in list(range(33080, 33101)) + [33090, 34121, 34120, 34122]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)
        try:
            s.connect_ex((HOST, port))
        except Exception:
            s.close()
            continue
        pend.append((port, s))
    deadline = time.time() + 1.0
    while pend and time.time() < deadline:
        _, w, _ = select.select([], [s for _, s in pend], [], 0.05)
        for p, s in w:
            err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err == 0:
                log('port %d OPEN' % p)
            s.close()
        pend = [(p, s) for p, s in pend if s.fileno() != -1]
    for p, s in pend:
        s.close()
    log('neighbor scan done')

    log('CFM90_DONE')
    f.close()


if __name__ == '__main__':
    main()
