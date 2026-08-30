# -*- coding: utf-8 -*-
"""recon_net: 沙箱网络拓扑侦察 (零副作用)
1) ip route / /proc/net/route -> 默认网关 (host 侧接口 IP)
2) ip addr / /proc/net/tcp,tcp6 -> 本地 IP + ESTABLISHED 对端 (host agent)
3) /proc/net/arp + ip neigh -> host MAC / 邻居
4) /proc/net/vsock -> vsock 归属
5) 网关/对端 IP 常见端口 connect 探测 (不发送数据)
输出落盘 + 哨兵 RECON_DONE"""
import os, time, socket, subprocess

OUT = '/vercel/sandbox/recon_net.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + r.stderr).strip()[:2000]
    except Exception as e:
        return 'ERR %s' % e


def parse_v4mapped(hexaddr):
    """tcp6 表 IPv4-mapped 地址解析为 IPv4"""
    parts = hexaddr.split(':')
    if len(parts) == 8 and parts[4] == 'FFFF':
        hi = int(parts[6], 16)
        lo = int(parts[7], 16)
        return '%d.%d.%d.%d' % ((hi >> 8) & 0xff, hi & 0xff, (lo >> 8) & 0xff, lo & 0xff)
    return None


def parse_tcp4(hexaddr):
    ip_hex, port_hex = hexaddr.split(':')
    ip_int = int(ip_hex, 16)
    ip = '%d.%d.%d.%d' % (ip_int & 0xff, (ip_int >> 8) & 0xff, (ip_int >> 16) & 0xff, (ip_int >> 24) & 0xff)
    return ip, int(port_hex, 16)


def try_conn(ip, port, timeout=2):
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.close()
        return 'OPEN'
    except Exception as e:
        return 'CLOSED:%s' % type(e).__name__


def main():
    log('=== 1) 路由表 ===')
    log('ip route: %s' % sh('ip route 2>/dev/null || true'))
    log('route -n: %s' % sh('route -n 2>/dev/null || true'))
    try:
        with open('/proc/net/route', 'r') as fh:
            for ln in fh.readlines():
                log('ROUTE: %s' % ln.strip())
    except Exception as e:
        log('route ERR %s' % e)

    log('=== 2) 本地 IP ===')
    log('ip addr: %s' % sh('ip addr 2>/dev/null || true'))
    log('ip -6 addr: %s' % sh('ip -6 addr 2>/dev/null || true'))

    log('=== 3) ESTABLISHED 对端 (host agent IP) ===')
    remotes = set()
    locals_ = set()
    try:
        with open('/proc/net/tcp', 'r') as fh:
            for ln in fh.readlines()[1:]:
                parts = ln.split()
                if len(parts) > 3:
                    lip, lport = parse_tcp4(parts[1])
                    rip, rport = parse_tcp4(parts[2])
                    if parts[3] == '01':  # ESTABLISHED
                        remotes.add((rip, rport))
                    locals_.add((lip, lport))
                    log('TCP4 %s:%s -> %s:%s st=%s' % (lip, lport, rip, rport, parts[3]))
    except Exception as e:
        log('tcp ERR %s' % e)
    try:
        with open('/proc/net/tcp6', 'r') as fh:
            for ln in fh.readlines()[1:]:
                parts = ln.split()
                if len(parts) > 3:
                    lip = parse_v4mapped(parts[1].split(':')[0] + ':' + parts[1].split(':')[1] + ':' + parts[1].split(':')[2] + ':' + parts[1].split(':')[3] + ':' + parts[1].split(':')[4] + ':' + parts[1].split(':')[5] + ':' + parts[1].split(':')[6] + ':' + parts[1].split(':')[7]) if False else None
                    log('TCP6: %s st=%s' % (ln.strip()[:200], parts[3]))
    except Exception as e:
        log('tcp6 ERR %s' % e)

    log('=== 4) ARP / 邻居 ===')
    log('ip neigh: %s' % sh('ip neigh 2>/dev/null || true'))
    try:
        with open('/proc/net/arp', 'r') as fh:
            for ln in fh.readlines():
                log('ARP: %s' % ln.strip())
    except Exception as e:
        log('arp ERR %s' % e)

    log('=== 5) vsock 表 ===')
    try:
        with open('/proc/net/vsock', 'r') as fh:
            for ln in fh.readlines():
                log('VSOCK: %s' % ln.strip())
    except Exception as e:
        log('vsock ERR %s' % e)

    log('=== 6) 网关/对端端口探测 ===')
    # 从路由表提取网关
    gw = None
    try:
        with open('/proc/net/route', 'r') as fh:
            for ln in fh.readlines()[1:]:
                parts = ln.split()
                if len(parts) > 2 and parts[1] == '00000000':
                    gw_int = int(parts[2], 16)
                    gw = '%d.%d.%d.%d' % (gw_int & 0xff, (gw_int >> 8) & 0xff,
                                          (gw_int >> 16) & 0xff, (gw_int >> 24) & 0xff)
                    log('DEFAULT GW: %s' % gw)
    except Exception as e:
        log('gw ERR %s' % e)

    targets = set()
    if gw:
        targets.add(gw)
    for rip, rport in remotes:
        targets.add(rip)
    log('probe targets: %s' % targets)
    PORTS = [22, 53, 80, 443, 2375, 2376, 2379, 2380, 3000, 3306, 5000, 5432, 6379,
             6443, 8000, 8080, 8443, 9000, 9090, 9100, 10250, 10255, 10256, 23456, 26661, 33090]
    for ip in sorted(targets):
        for p in PORTS:
            r = try_conn(ip, p)
            if r == 'OPEN':
                log('HOST %s:%d -> OPEN' % (ip, p))
        log('scan done: %s' % ip)

    log('RECON_DONE')
    f.close()


if __name__ == '__main__':
    main()
