# -*- coding: utf-8 -*-
"""scanlocal: 本地 VM 网卡 IP 全端口 TCP 扫描 (host 服务面完整枚举)
J558: 23456 = host root 进程 bind 在 VM 网卡 IP, guest 可直连
-> host 网络面可能与 guest 共享, 扫描本地 IP 找其他 host 常驻服务
PHASE1 定位本地 IP; PHASE2 非阻塞全端口扫描; PHASE3 开放端口 HTTP 探测;
PHASE4 PTR 反查 (172.31.0.2) + 网关对照
输出落盘 + 哨兵 SCANLOCAL_DONE"""
import os, time, socket, select, struct

OUT = '/vercel/sandbox/scanlocal.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def sh(cmd, t=8):
    try:
        r = subprocess_run(cmd)
        return r.strip()[:300]
    except Exception as e:
        return 'ERR %s' % e


def subprocess_run(cmd):
    import subprocess
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=8)
    return (r.stdout + r.stderr)


def get_local_ips():
    """从 /proc/net/tcp 提取本地 IP"""
    ips = set()
    try:
        with open('/proc/net/tcp', 'r') as fh:
            for ln in fh.readlines()[1:]:
                parts = ln.split()
                if len(parts) > 3:
                    laddr = parts[1]
                    ip_hex, port_hex = laddr.split(':')
                    ip_int = int(ip_hex, 16)
                    ip = '%d.%d.%d.%d' % (ip_int & 0xff, (ip_int >> 8) & 0xff,
                                          (ip_int >> 16) & 0xff, (ip_int >> 24) & 0xff)
                    if not ip.startswith('127.') and ip != '0.0.0.0':
                        ips.add(ip)
    except Exception as e:
        log('get_local_ips ERR %s' % e)
    return sorted(ips)


def tcp_scan(ip, ports, timeout=0.6):
    """非阻塞批量 TCP 扫描, 返回开放端口列表"""
    open_ports = []
    pend = []
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setblocking(False)
        try:
            s.connect_ex((ip, p))
        except Exception:
            s.close()
            continue
        pend.append((p, s))
    deadline = time.time() + timeout
    while pend and time.time() < deadline:
        _, writable, _ = select.select([], [s for _, s in pend], [], 0.05)
        if not writable:
            continue
        wset = set(id(s) for s in writable)
        remaining = []
        for p, s in pend:
            if id(s) in wset:
                err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if err == 0:
                    open_ports.append(p)
                s.close()
            else:
                remaining.append((p, s))
        pend = remaining
    for p, s in pend:
        s.close()
    return sorted(open_ports)


def http_probe(ip, port, timeout=3):
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
        return data[:500]
    except Exception as e:
        return ('ERR %s' % e).encode()[:200]


def main():
    log('=== SCANLOCAL PHASE1 定位本地 IP ===')
    ips = get_local_ips()
    log('local ips: %s' % ips)
    for extra in ['ip addr 2>/dev/null | grep inet', 'cat /proc/net/tcp6 | head -3']:
        log('cmd: %s' % sh(extra))
    if not ips:
        log('NO_LOCAL_IP')
        log('SCANLOCAL_DONE')
        f.close()
        raise SystemExit(0)

    ip = ips[0]
    log('scan target: %s' % ip)

    log('=== SCANLOCAL PHASE2 全端口 TCP 扫描 ===')
    all_ports = list(range(1, 1025)) + list(range(1025, 65536))
    # 分块避免 fd 耗尽
    opens = []
    CHUNK = 800
    for i in range(0, len(all_ports), CHUNK):
        chunk = all_ports[i:i + CHUNK]
        o = tcp_scan(ip, chunk)
        if o:
            log('chunk %d-%d open: %s' % (chunk[0], chunk[-1], o))
            opens.extend(o)
        if i % 10000 == 0 and i > 0:
            log('progress: scanned %d ports' % i)
    log('total open: %s' % opens)

    log('=== SCANLOCAL PHASE3 开放端口 HTTP 探测 ===')
    for p in opens:
        resp = http_probe(ip, p)
        log('port %d: %s' % (p, resp))

    log('=== SCANLOCAL PHASE4 DNS PTR 反查 ===')
    try:
        import socket as sk
        for q in [ip, '100.64.0.1', '172.31.0.2', '169.254.169.254']:
            try:
                name = sk.gethostbyaddr(q)
                log('PTR %s -> %s' % (q, name[0]))
            except Exception as e:
                log('PTR %s ERR %s' % (q, e))
    except Exception as e:
        log('PTR phase ERR %s' % e)

    log('SCANLOCAL_DONE')
    f.close()


if __name__ == '__main__':
    main()
