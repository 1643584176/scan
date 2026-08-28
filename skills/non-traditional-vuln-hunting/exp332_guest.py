# -*- coding: utf-8 -*-
"""exp_j332: 主动探测邻居 fe80::78b2:a8ff:fed9:8f1a (MAC 7a:b2:a8:d9:8f:1a)
1) ping6 邻居 2) 端口扫描(link-local 直连) 3) 监听 30s 抓它的数据帧 4) ND 表复查"""
import socket, struct, time, os, subprocess

OUT = '/vercel/sandbox/arp332.out'
NEIGH = 'fe80::78b2:a8ff:fed9:8f1a%eth0'


def log(*a):
    try:
        with open(OUT, 'a') as f:
            f.write(' '.join(str(x) for x in a) + '\n')
    except Exception:
        pass


def shell(cmdline, t=8):
    try:
        r = subprocess.run(cmdline, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return 'ERR: %s' % e


def tcp_probe(ip6, ports):
    """对 link-local 邻居做 TCP connect 扫描"""
    for p in ports:
        try:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            s.settimeout(2)
            r = s.connect_ex((ip6, p, 0, 0))
            log('TCP', p, 'connect_ex=%d' % r)
            if r == 0:
                s.close()
                log('TCP_OPEN', p)
        except Exception as e:
            log('TCP_ERR', p, repr(e))
        time.sleep(0.3)


def listen(duration=30):
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        s.settimeout(2)
        end = time.time() + duration
        seen = set()
        while time.time() < end:
            try:
                data, addr = s.recvfrom(65535)
                if len(data) < 14:
                    continue
                src_mac = ':'.join('%02x' % b for b in data[6:12])
                if src_mac in ('7a:b2:a8:d9:8f:1a', 'aa:d4:ea:5b:10:7c'):
                    if len(data) >= 14 + 40:
                        src6 = socket.inet_ntop(socket.AF_INET6, data[22:38])
                        dst6 = socket.inet_ntop(socket.AF_INET6, data[38:54])
                        nh = data[20]
                        log('NEIGH_V6', src_mac, src6, '->', dst6, 'nh=%d' % nh)
                        # ICMPv6 类型
                        if nh == 58 and len(data) >= 14 + 40 + 2:
                            log('  icmp6_type=%d' % data[14 + 40])
                    else:
                        log('NEIGH_OTHER', src_mac, 'proto=0x%04x' % addr[1])
                    seen.add((src_mac, addr[1]))
                # 网关 ARP 变化
                if addr[1] == 0x0806:
                    log('ARP_FRAME', src_mac)
            except socket.timeout:
                continue
        s.close()
        log('LISTEN_DONE unique=%d' % len(seen))
    except Exception as e:
        log('ERR', repr(e))


if __name__ == '__main__':
    try:
        os.remove(OUT)
    except Exception:
        pass
    log('=== PING6 邻居 ===')
    log(shell('ping6 -c 3 -W 2 %s 2>&1 | tail -5' % NEIGH, 10))
    log('=== TCP 扫描(常见端口) ===')
    tcp_probe('fe80::78b2:a8ff:fed9:8f1a', [22, 53, 80, 443, 23456, 26661, 30001, 30002, 8080, 9090])
    log('=== 邻居表 ===')
    log(shell('cat /proc/net/ndisc_cache 2>/dev/null | head -20; echo ---; ip -6 neigh 2>/dev/null | head -20'))
    log('=== 监听 30s 抓邻居流量 ===')
    listen(30)
    log('=== 邻居表(监听后) ===')
    log(shell('ip -6 neigh 2>/dev/null | head -20'))
    log('SCAN_DONE')
