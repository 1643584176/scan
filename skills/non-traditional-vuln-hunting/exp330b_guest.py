# -*- coding: utf-8 -*-
"""exp_j330b: 仅 promiscuous 监听 35s, 找同广播域其他 cell 流量"""
import socket, struct, time, os, fcntl

OUT = '/vercel/sandbox/arp330b.out'


def log(*a):
    try:
        with open(OUT, 'a') as f:
            f.write(' '.join(str(x) for x in a) + '\n')
    except Exception:
        pass


def promisc_listen(duration=35):
    try:
        # 不支持 promiscuous(EINVAL), 普通模式也能收广播/多播帧
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        s.settimeout(2)
        end = time.time() + duration
        seen = set()
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
                if proto == 0x0800 and len(data) >= 34:
                    src_ip = socket.inet_ntoa(data[26:30])
                    dst_ip = socket.inet_ntoa(data[30:34])
                    key = ('IP', src_mac, src_ip)
                    if key not in seen:
                        seen.add(key)
                        log('PROM_IP', src_mac, src_ip, '->', dst_ip)
                elif proto == 0x0806 and len(data) >= 42:
                    arp_oper = struct.unpack('!H', data[20:22])[0]
                    sp = socket.inet_ntoa(data[28:32])
                    tp = socket.inet_ntoa(data[38:42])
                    key = ('ARP', src_mac, sp)
                    if key not in seen:
                        seen.add(key)
                        log('PROM_ARP', src_mac, sp, '->', tp, 'oper=%d' % arp_oper)
                else:
                    key = ('O', src_mac)
                    if key not in seen:
                        seen.add(key)
                        log('PROM_OTHER', src_mac, 'proto=0x%04x' % proto)
            except socket.timeout:
                continue
        s.close()
        log('PROM_DONE total=%d unique=%d' % (total, len(seen)))
    except Exception as e:
        log('PROM_ERR', repr(e))


if __name__ == '__main__':
    try:
        os.remove(OUT)
    except Exception:
        pass
    log('START')
    promisc_listen(35)
    log('SCAN_DONE')
