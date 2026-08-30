# -*- coding: utf-8 -*-
"""guest_udp: deny-all 下 UDP 非 DNS 出网验证 (规则原文: 只拦 outbound TCP 和 DNS)
1) NTP 回显 (time.nist.gov:123, UDP 非 DNS) - 有响应 = 出网
2) QUIC 探测 (1.1.1.1:443 UDP)
3) DNS 对照 (8.8.8.8:53, 应放行)
4) 普通 UDP (1.1.1.1:53 非 DNS 内容)
输出落盘 + 哨兵 UDP_DONE"""
import socket, struct, time, os, subprocess

OUT = '/vercel/sandbox/udp_probe.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


def udp_send(ip, port, payload, label, t=6):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(t)
        s.sendto(payload, (ip, port))
        try:
            data, addr = s.recvfrom(2048)
            log('[%s] SEND_OK RECV %dB from %s' % (label, len(data), addr))
            return data
        except socket.timeout:
            log('[%s] SEND_OK NO_RESP' % label)
            return b''
    except Exception as e:
        log('[%s] EXC %s' % (label, type(e).__name__))
        return b''


log('=== UDP 非 DNS 出网测试 (deny-all) ===')
# 1) NTP 回显 - UDP:123 非 DNS
ntp_req = b'\x1b' + 47 * b'\x00'
udp_send('time.nist.gov', 123, ntp_req, 'NTP-time.nist.gov:123', 6)
udp_send('time.google.com', 123, ntp_req, 'NTP-time.google.com:123', 6)
udp_send('ntp.aliyun.com', 123, ntp_req, 'NTP-ntp.aliyun.com:123', 6)

# 2) QUIC/TLS UDP 到 443
quic_initial = bytes.fromhex('c00000000108') + b'\x00' * 32
udp_send('1.1.1.1', 443, quic_initial, 'QUIC-1.1.1.1:443', 6)
udp_send('8.8.8.8', 443, quic_initial, 'QUIC-8.8.8.8:443', 6)

# 3) DNS 对照 (UDP:53, 应放行)
dns_req = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'
udp_send('8.8.8.8', 53, dns_req, 'DNS-8.8.8.8:53', 6)

# 4) 普通 UDP 非标准服务 (1.1.1.1:53 发非 DNS 数据)
udp_send('1.1.1.1', 53, b'NOTDNS' + b'\x00' * 20, 'UDP-1.1.1.1:53-nondns', 5)

# 5) 本机/网关 UDP (参照)
udp_send('127.0.0.1', 123, ntp_req, 'UDP-localhost:123', 3)

log('=== 附加: TCP 对照 (应全拦) ===')
for ip, port in [('1.1.1.1', 443), ('8.8.8.8', 53)]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        r = s.connect_ex((ip, port))
        log('[TCP %s:%d] connect_ex=%d' % (ip, port, r))
        s.close()
    except Exception as e:
        log('[TCP %s:%d] EXC %s' % (ip, port, type(e).__name__))

log('UDP_DONE')
f.close()
