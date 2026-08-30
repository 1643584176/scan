# -*- coding: utf-8 -*-
"""scanlocal2: tcp6 表全量解析 + 本地 IP 全端口扫描 (host 服务面)
J558: 23456 host root 监听在共享 netns, v4 表为空 -> 全部在 tcp6 (dual-stack)
PHASE1 tcp6 全表 dump (uid 判定监听者); PHASE2 提取本地 IP 扫描全端口;
PHASE3 开放端口 HTTP 探测; PHASE4 PTR 反查
输出落盘 + 哨兵 SCANL2_DONE"""
import os, time, socket, select, struct, re

OUT = '/vercel/sandbox/scanl2.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def ipv6_to_str(hex6):
    """从 tcp6 地址提取 v4 (最后 32 位) 或返回 v6 字符串"""
    h = hex6.replace(':', '')
    if len(h) >= 8 and h[-8:].replace('0', '') == '':
        return '::'
    if len(h) >= 8:
        # 最后 32 位 = v4 (适用于 v4-mapped 及内核其他映射格式)
        return '%d.%d.%d.%d' % (int(h[-8:-6], 16), int(h[-6:-4], 16),
                                int(h[-4:-2], 16), int(h[-2:], 16))
    return hex6


def parse_tcp6():
    """解析 /proc/net/tcp6, 返回 [(laddr, lport, raddr, rport, st, uid, inode)]"""
    rows = []
    try:
        with open('/proc/net/tcp6', 'r') as fh:
            lines = fh.readlines()
        for ln in lines[1:]:
            parts = ln.split()
            if len(parts) >= 10:
                laddr_hex, lport_hex = parts[1].split(':')
                raddr_hex, rport_hex = parts[2].split(':')
                st = parts[3]
                uid = parts[7]
                inode = parts[9]
                rows.append((ipv6_to_str(laddr_hex), int(lport_hex, 16),
                             ipv6_to_str(raddr_hex), int(rport_hex, 16),
                             st, uid, inode))
    except Exception as e:
        log('parse tcp6 ERR %s' % e)
    return rows


def tcp_scan(ip, ports, timeout=0.5, is_v6=False):
    open_ports = []
    fam = socket.AF_INET6 if is_v6 else socket.AF_INET
    pend = []
    for p in ports:
        s = socket.socket(fam, socket.SOCK_STREAM)
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
    # 二次验证: 真实 connect 确认
    confirmed = []
    for p in sorted(open_ports):
        try:
            s = socket.socket(fam, socket.SOCK_STREAM)
            s.settimeout(1.5)
            s.connect((ip, p))
            s.close()
            confirmed.append(p)
        except Exception:
            pass
    return confirmed


def http_probe(ip, port, timeout=3, is_v6=False):
    try:
        fam = socket.AF_INET6 if is_v6 else socket.AF_INET
        s = socket.socket(fam, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
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
    log('=== SCANL2 PHASE1 tcp6 全表 ===')
    rows = parse_tcp6()
    log('tcp6 rows: %d' % len(rows))
    for r in rows:
        log('  %s:%d -> %s:%d st=%s uid=%s inode=%s' % (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))

    # 提取候选目标: 本地监听/连接地址 + 远端 host 地址
    local_ips = set()
    remote_ips = set()
    for r in rows:
        if r[0] not in ('::', '0.0.0.0', '::1') and r[4] != '0A':
            local_ips.add(r[0])
        if r[2] not in ('::', '0.0.0.0', '::1') and r[2] and r[4] == '01':
            remote_ips.add(r[2])
    log('candidate local ips: %s' % local_ips)
    log('candidate remote ips (ESTABLISHED): %s' % remote_ips)

    targets = []
    for ip in sorted(local_ips):
        if ':' not in ip:
            targets.append((ip, False))
    # 127.0.0.1 可到达 host bind 全零服务 (J559 已证)
    for ip, is6 in [('127.0.0.1', False), ('::1', True)]:
        if ip not in [t[0] for t in targets]:
            targets.append((ip, is6))

    log('=== SCANL2 PHASE2 全端口扫描 ===')
    all_ports = list(range(1, 65536))
    for ip, is6 in targets:
        opens = []
        for i in range(0, len(all_ports), 800):
            chunk = all_ports[i:i + 800]
            o = tcp_scan(ip, chunk, is_v6=is6)
            if o:
                opens.extend(o)
                log('chunk %d-%d open: %s' % (chunk[0], chunk[-1], o))
        log('target %s (v6=%s) OPEN PORTS: %s' % (ip, is6, opens))
        for p in opens:
            resp = http_probe(ip, p, is_v6=is6)
            log('  probe %s:%d -> %s' % (ip, p, resp))

    log('=== SCANL2 PHASE3 PTR 反查 ===')
    try:
        for q in ['100.64.0.1', '172.31.0.2', '169.254.169.254'] + sorted(remote_ips):
            try:
                name = socket.gethostbyaddr(q)
                log('PTR %s -> %s' % (q, name[0]))
            except Exception as e:
                log('PTR %s ERR %s' % (q, e))
    except Exception as e:
        log('PTR phase ERR %s' % e)

    log('SCANL2_DONE')
    f.close()


if __name__ == '__main__':
    main()
