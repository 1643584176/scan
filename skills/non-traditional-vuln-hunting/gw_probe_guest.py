# -*- coding: utf-8 -*-
"""gw_probe: custom 模式下探测真实网关 100.64.0.1 (host 接口) 的服务面
1) 100.64.0.1 常见服务端口 + 1-1024 全端口 (非阻塞分批)
2) 100.64.0.0/28 各 IP 常见端口 (host 其他接口?)
3) OPEN 端口发轻量 banner (HTTP/SSH/TLS 指纹), 区分真实服务 vs 防火墙模拟
输出落盘 + 哨兵 GWPROBE_DONE"""
import socket, select, time, struct

OUT = '/vercel/sandbox/gwprobe.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def tcp_scan(ip, ports, timeout=1.2, batch=200):
    """非阻塞批量 TCP 扫描, 返回开放端口列表"""
    open_ports = []
    for i in range(0, len(ports), batch):
        chunk = ports[i:i + batch]
        pend = []
        for p in chunk:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setblocking(False)
                s.connect_ex((ip, p))
                pend.append((p, s))
            except Exception:
                try:
                    s.close()
                except Exception:
                    pass
        deadline = time.time() + timeout
        while pend and time.time() < deadline:
            try:
                _, writable, _ = select.select([], [s for _, s in pend], [], 0.05)
            except Exception:
                break
            if not writable:
                continue
            wset = set(id(s) for s in writable)
            remaining = []
            for p, s in pend:
                if id(s) in wset:
                    try:
                        err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                        if err == 0:
                            open_ports.append(p)
                    except Exception:
                        pass
                    s.close()
                else:
                    remaining.append((p, s))
            pend = remaining
        for p, s in pend:
            try:
                s.close()
            except Exception:
                pass
        time.sleep(0.2)
    return sorted(open_ports)


def banner(ip, port, timeout=3):
    """轻量 banner: 尝试 HTTP GET / TLS ClientHello / SSH 版本"""
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.settimeout(timeout)
        # HTTP
        try:
            s.sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
            d = s.recv(300)
            if d:
                s.close()
                return 'HTTP: ' + repr(d[:120])
        except Exception:
            pass
        try:
            s = socket.create_connection((ip, port), timeout=timeout)
            s.settimeout(timeout)
            s.sendall(b'\x16\x03\x01\x00\x05\x01\x00\x00\x01\x00')  # TLS ClientHello
            d = s.recv(300)
            if d:
                s.close()
                return 'TLS: ' + repr(d[:80])
        except Exception:
            pass
        try:
            s = socket.create_connection((ip, port), timeout=timeout)
            s.settimeout(timeout)
            d = s.recv(200)  # 部分协议先发 banner (SSH/MySQL)
            if d:
                s.close()
                return 'BANNER: ' + repr(d[:120])
        except Exception:
            pass
        s.close()
        return 'NODATA'
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


def main():
    GW = '100.64.0.1'
    log('=== PHASE1 100.64.0.1 常见服务端口 ===')
    common = [22, 53, 80, 443, 2375, 2376, 2379, 2380, 3000, 3306, 5000, 5432, 6379,
              6443, 8000, 8080, 8443, 9000, 9090, 9100, 10250, 10255, 10256, 11211,
              17000, 23456, 26661, 33090, 34121, 50000, 65535]
    o = tcp_scan(GW, common, timeout=1.5)
    log('common open: %s' % o)
    for p in o:
        log('banner %s:%d -> %s' % (GW, p, banner(GW, p)))
        time.sleep(0.3)

    log('=== PHASE2 100.64.0.1 1-1024 全端口 ===')
    o2 = tcp_scan(GW, list(range(1, 1025)), timeout=1.2, batch=150)
    log('low ports open: %s' % o2)
    for p in o2:
        log('banner %s:%d -> %s' % (GW, p, banner(GW, p)))
        time.sleep(0.3)

    log('=== PHASE3 100.64.0.0/28 常见端口 ===')
    for i in range(2, 17):
        ip = '100.64.0.%d' % i
        o3 = tcp_scan(ip, common, timeout=1.0, batch=100)
        if o3:
            log('%s open: %s' % (ip, o3))
            for p in o3:
                log('banner %s:%d -> %s' % (ip, p, banner(ip, p)))
                time.sleep(0.3)
        else:
            log('%s: none' % ip)
        time.sleep(0.3)

    log('GWPROBE_DONE')
    f.close()


if __name__ == '__main__':
    main()
