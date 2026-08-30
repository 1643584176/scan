# -*- coding: utf-8 -*-
"""guest_udp2: deny-all 下 UDP 出网验证 v2 - IP 直连回显协议
1) NTP IP 直连 (162.159.200.123:123 / 216.239.35.0:123) - 有 48B 响应 = 出网
2) IPv6 UDP (2001:4860:4860::8888:53 DNS)
3) 网关 UDP 探测
4) ICMP 对照
输出落盘 + 哨兵 UDP2_DONE"""
import socket, struct, time, os

OUT = '/vercel/sandbox/udp2_probe.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


def udp_send(family, ip, port, payload, label, t=6):
    try:
        s = socket.socket(family, socket.SOCK_DGRAM)
        s.settimeout(t)
        s.sendto(payload, (ip, port))
        try:
            data, addr = s.recvfrom(2048)
            log('[%s] RECV %dB from %s hex=%s' % (label, len(data), addr, data[:16].hex()))
            return data
        except socket.timeout:
            log('[%s] NO_RESP' % label)
            return b''
    except Exception as e:
        log('[%s] EXC %s' % (label, type(e).__name__))
        return b''


ntp_req = b'\x1b' + 47 * b'\x00'
log('=== UDP NTP IP 直连 (deny-all) ===')
udp_send(socket.AF_INET, '162.159.200.123', 123, ntp_req, 'NTP-162.159.200.123', 6)
udp_send(socket.AF_INET, '216.239.35.0', 123, ntp_req, 'NTP-216.239.35.0', 6)
udp_send(socket.AF_INET, '129.6.15.28', 123, ntp_req, 'NTP-129.6.15.28', 6)
udp_send(socket.AF_INET, '64.90.182.55', 123, ntp_req, 'NTP-64.90.182.55', 6)

log('=== UDP 其他回显 ===')
# OpenNTP 项目 (开放 UDP 回显: port 123 之外)
udp_send(socket.AF_INET, '8.8.8.8', 53, b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01', 'DNS-8.8.8.8:53', 6)
# UDP 443 TLS 包 (QUIC 服务器可能回 Retry)
quic = bytes.fromhex('c00000000108') + b'\x00' * 32 + b'\x00' * 100
udp_send(socket.AF_INET, '1.1.1.1', 443, quic, 'QUIC-1.1.1.1:443', 6)

log('=== IPv6 UDP ===')
udp_send(socket.AF_INET6, '2001:4860:4860::8888', 53, b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01', 'DNS6-2001:4860:4860::8888', 6)
udp_send(socket.AF_INET6, '2606:4700:4700::1111', 53, b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01', 'DNS6-2606:4700:4700::1111', 6)

log('=== 本机接口信息 ===')
try:
    r = os.popen('ip addr 2>/dev/null | grep -E "inet |inet6 "').read()
    log('addrs:\n%s' % r)
except Exception as e:
    log('ip err %s' % e)

log('=== ICMP 对照 ===')
try:
    import subprocess
    r = subprocess.run(['ping', '-c', '2', '-W', '3', '8.8.8.8'], capture_output=True, text=True, timeout=12)
    log('ping rc=%d %s' % (r.returncode, (r.stdout + r.stderr)[-200:].replace('\n', ' ')))
except Exception as e:
    log('ping EXC %s' % e)

log('UDP2_DONE')
f.close()
