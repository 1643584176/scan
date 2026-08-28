# -*- coding: utf-8 -*-
"""exp_j331: 深挖未知 MAC aa:d4:ea:5b:10:7c
1) 完整 IPv6 帧解析(源/目的地址+协议) 2) ndisc/路由表 dump 3) IPv6 多播邻居发现"""
import socket, struct, time, os, subprocess

OUT = '/vercel/sandbox/arp331.out'


def log(*a):
    try:
        with open(OUT, 'a') as f:
            f.write(' '.join(str(x) for x in a) + '\n')
    except Exception:
        pass


def shell(cmdline, t=5):
    try:
        r = subprocess.run(cmdline, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return 'ERR: %s' % e


def parse_ip6(src_mac, data):
    """解析 IPv6 帧, 返回 (src_ip6, dst_ip6, nexthdr)"""
    if len(data) < 40:
        return None
    src6 = socket.inet_ntop(socket.AF_INET6, data[8:24])
    dst6 = socket.inet_ntop(socket.AF_INET6, data[24:40])
    nh = data[6]
    return src6, dst6, nh


def listen(duration=40):
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        s.settimeout(2)
        end = time.time() + duration
        seen = {}
        total = 0
        while time.time() < end:
            try:
                data, addr = s.recvfrom(65535)
                ifn = addr[0]
                proto = addr[1]
                total += 1
                if len(data) < 14:
                    continue
                src_mac = ':'.join('%02x' % b for b in data[6:12])
                key = (src_mac, proto)
                seen[key] = seen.get(key, 0) + 1
                if proto == 0x86dd:  # IPv6
                    p = parse_ip6(src_mac, data[14:])
                    if p:
                        log('V6', src_mac, p[0], '->', p[1], 'nh=%d' % p[2])
                    else:
                        log('V6_SHORT', src_mac)
                elif proto == 0x0800 and len(data) >= 34:
                    src_ip = socket.inet_ntoa(data[26:30])
                    log('V4', src_mac, src_ip)
                elif proto == 0x0806:
                    log('ARP', src_mac)
            except socket.timeout:
                continue
        s.close()
        log('DONE total=%d' % total)
        for k, v in sorted(seen.items(), key=lambda x: -x[1]):
            log('STAT', k[0], hex(k[1]), v)
    except Exception as e:
        log('ERR', repr(e))


if __name__ == '__main__':
    try:
        os.remove(OUT)
    except Exception:
        pass
    # 1. 系统表 dump
    log('=== ndisc_cache ===')
    log(shell('cat /proc/net/ndisc_cache 2>/dev/null || cat /proc/net/ndisc 2>/dev/null || echo NO_NDISC'))
    log('=== ipv6_route ===')
    log(shell('cat /proc/net/ipv6_route'))
    log('=== ipv6 addr ===')
    log(shell('cat /proc/net/if_inet6'))
    # 2. 监听 40s
    log('=== LISTEN 40s ===')
    listen(40)
    # 3. ICMPv6 邻居发现(ff02::1 多播) — 需要 root/CAP_NET_RAW
    log('=== PING ff02::1 ===')
    log(shell('ping6 -c 2 -W 2 ff02::1 2>&1 | head -20', 8))
    log(shell('ping -6 -c 2 -W 2 ff02::1 2>&1 | head -20', 8))
    log('SCAN_DONE')
