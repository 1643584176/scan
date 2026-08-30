# -*- coding: utf-8 -*-
"""scanl5: 新沙箱确认 host 端口面 (33090/34121 是否常驻)
PHASE1 本地 IP 定位 (tcp6 表); PHASE2 全端口扫描 (确认开放集);
PHASE3 对 33090/34121 HTTP 探测确认服务; PHASE4 PTR 反查
输出落盘 + 哨兵 SCANL5_DONE"""
import os, time, socket, select

OUT = '/vercel/sandbox/scanl5.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def get_local_v4():
    """从 tcp6 表提取本地 v4 IP (最后 32 位大端)"""
    ips = set()
    try:
        with open('/proc/net/tcp6', 'r') as fh:
            lines = fh.readlines()
        for ln in lines[1:]:
            parts = ln.split()
            if len(parts) >= 10:
                laddr_hex = parts[1].split(':')[0].replace(':', '')
                lport = int(parts[1].split(':')[1], 16)
                if laddr_hex[-8:].replace('0', '') == '':
                    continue
                ip = '%d.%d.%d.%d' % (int(laddr_hex[-8:-6], 16), int(laddr_hex[-6:-4], 16),
                                      int(laddr_hex[-4:-2], 16), int(laddr_hex[-2:], 16))
                ips.add(ip)
    except Exception as e:
        log('tcp6 ERR %s' % e)
    return sorted(ips)


def tcp_scan(ip, ports, timeout=0.5):
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
        _, w, _ = select.select([], [s for _, s in pend], [], 0.05)
        if not w:
            continue
        wset = set(id(s) for s in w)
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
    # 二次验证
    confirmed = []
    for p in sorted(open_ports):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((ip, p))
            s.close()
            confirmed.append(p)
        except Exception:
            pass
    return confirmed


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
                if len(data) > 1500:
                    break
        except socket.timeout:
            pass
        s.close()
        return data[:400]
    except Exception as e:
        return ('ERR %s' % e).encode()[:150]


def main():
    log('=== SCANL5 PHASE1 本地 IP ===')
    ips = get_local_v4()
    log('local ips: %s' % ips)
    if not ips:
        log('NO_IP SCANL5_DONE')
        f.close()
        raise SystemExit(0)
    ip = ips[0]
    log('target: %s' % ip)

    log('=== SCANL5 PHASE2 全端口扫描 ===')
    opens = []
    all_ports = list(range(1, 65536))
    for i in range(0, len(all_ports), 800):
        chunk = all_ports[i:i + 800]
        o = tcp_scan(ip, chunk)
        if o:
            opens.extend(o)
            log('chunk %d open: %s' % (chunk[0], o))
    log('ALL OPEN: %s' % opens)

    log('=== SCANL5 PHASE3 服务确认 ===')
    for p in opens:
        r = http_probe(ip, p)
        log('port %d: %s' % (p, r))

    log('=== SCANL5 PHASE4 PTR ===')
    for q in [ip, '100.64.0.1']:
        try:
            log('PTR %s -> %s' % (q, socket.gethostbyaddr(q)[0]))
        except Exception as e:
            log('PTR %s ERR %s' % (q, e))

    log('SCANL5_DONE')
    f.close()


if __name__ == '__main__':
    main()
