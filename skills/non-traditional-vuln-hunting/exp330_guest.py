# -*- coding: utf-8 -*-
"""exp_j330: ARP 广播扫 /24 + promiscuous 25s 监听 eth0, 找同广播域其他 cell
在沙箱内执行。输出落盘 + SCAN_DONE 哨兵。"""
import socket, struct, time, os, fcntl

OUT = '/vercel/sandbox/arp330.out'


def log(*a):
    try:
        with open(OUT, 'a') as f:
            f.write(' '.join(str(x) for x in a) + '\n')
    except Exception:
        pass


def get_iface_info():
    for ifname in ['eth0', 'ens3', 'enp0s1']:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915,
                                              struct.pack('256s', ifname[:15].encode()))[20:24])
            mac = ':'.join('%02x' % b for b in fcntl.ioctl(s.fileno(), 0x8927,
                                                           struct.pack('256s', ifname[:15].encode()))[18:24])
            log('IFACE', ifname, ip, mac)
            return ifname, ip, mac
        except OSError:
            continue
    return None, None, None


def arp_scan(ifname, src_mac, src_ip, target_net):
    """对 target_net/24 逐个发 ARP 请求, 收响应者 MAC/IP"""
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
        s.bind((ifname, 0))
        s.settimeout(0.3)
        src_mac_b = bytes.fromhex(src_mac.replace(':', ''))
        base = '.'.join(target_net.split('.')[:3])
        for i in range(1, 255):
            dst = '%s.%d' % (base, i)
            eth = struct.pack('!6s6sH', b'\xff' * 6, src_mac_b, 0x0806)
            arp = struct.pack('!HHBBH6s4s6s4s', 1, 0x0800, 6, 4, 1, src_mac_b,
                              socket.inet_aton(src_ip), b'\x00' * 6, socket.inet_aton(dst))
            try:
                s.send(eth + arp)
            except Exception as e:
                log('SEND_ERR', dst, repr(e))
                continue
            try:
                data, _ = s.recvfrom(4096)
                if len(data) >= 42:
                    resp_mac = ':'.join('%02x' % b for b in data[6:12])
                    arp_oper = struct.unpack('!H', data[20:22])[0]
                    if arp_oper == 2:  # ARP reply
                        resp_ip = socket.inet_ntoa(data[28:32])
                        log('ARP', resp_ip, resp_mac)
            except socket.timeout:
                pass
        s.close()
        log('ARP_DONE', target_net)
    except Exception as e:
        log('ARP_ERR', target_net, repr(e))


def promisc_listen(ifname, duration=25):
    """promiscuous 监听: 抓所有以太网帧, 记录源 MAC 和 IPv4 源"""
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        # PACKET_ADD_MEMBERSHIP=1, PACKET_MR_PROMISC=1, SOL_PACKET=263
        mreq = struct.pack('IHH', 1, 0, 0)
        s.setsockopt(263, 1, mreq)
        s.settimeout(2)
        end = time.time() + duration
        seen = set()
        while time.time() < end:
            try:
                data, (ifn, proto, pkttype, hatype, halen, addr) = s.recvfrom(65535)
                if len(data) < 14:
                    continue
                src_mac = ':'.join('%02x' % b for b in data[6:12])
                if proto == 0x0800 and len(data) >= 34:
                    src_ip = socket.inet_ntoa(data[26:30])
                    key = (src_mac, src_ip)
                    if key not in seen:
                        seen.add(key)
                        log('PROM', src_mac, src_ip)
                elif proto == 0x0806 and len(data) >= 42:
                    arp_oper = struct.unpack('!H', data[20:22])[0]
                    sp = socket.inet_ntoa(data[28:32])
                    key = (src_mac, sp)
                    if key not in seen:
                        seen.add(key)
                        log('PROM_ARP', src_mac, sp, 'oper=%d' % arp_oper)
                else:
                    if src_mac not in seen:
                        seen.add(src_mac)
                        log('PROM_OTHER', src_mac, 'proto=%d' % proto)
            except socket.timeout:
                continue
        s.close()
        log('PROM_DONE')
    except Exception as e:
        log('PROM_ERR', repr(e))


if __name__ == '__main__':
    try:
        os.remove(OUT)
    except Exception:
        pass
    ifn, ip, mac = get_iface_info()
    if not ifn:
        log('NO_IFACE')
    else:
        log('MY', ifn, ip, mac)
        # 扫本机所在 /24
        arp_scan(ifn, mac, ip, ip)
        # 也扫网关段 100.64.0.0/24
        arp_scan(ifn, mac, ip, '100.64.0.0')
        # promiscuous 监听 25s
        promisc_listen(ifn, 25)
    log('SCAN_DONE')
