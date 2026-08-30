# -*- coding: utf-8 -*-
"""udp6_probe: custom 模式下 UDP 面 + IPv6 面探测
UDP: 私有网段 53/123/53 非 DNS 端口 / 公网 53 对照
IPv6: 公网 (2001:4860:8888) / 私网 (fd00::1, fe80::1) / DNS IPv6
输出落盘 + 哨兵 UDP6_DONE"""
import socket, time, struct

OUT = '/vercel/sandbox/udp6.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def udp_send(ip, port, payload, t=2.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(t)
        s.sendto(payload, (ip, port))
        try:
            d, _ = s.recvfrom(2048)
            return 'RESP %d %r' % (len(d), d[:40])
        except socket.timeout:
            return 'SENT_NORESP'
        finally:
            s.close()
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


def tcp6(ip, port, t=2.0):
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        s.close()
        return 'OPEN'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


def udp6_send(ip, port, payload, t=2.0):
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        s.settimeout(t)
        s.sendto(payload, (ip, port))
        try:
            d, _ = s.recvfrom(2048)
            return 'RESP %d' % len(d)
        except socket.timeout:
            return 'SENT_NORESP'
        finally:
            s.close()
    except OSError as e:
        return 'OSERR:%s' % e.errno


log('START')
# P1 UDP 私有网段
log('U1 172.31.0.2:53 DNS -> %s' % udp_send('172.31.0.2', 53, b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'))
log('U2 172.31.0.2:123 NTP -> %s' % udp_send('172.31.0.2', 123, b'\x1b' + b'\x00' * 47))
log('U3 172.31.0.3:53 -> %s' % udp_send('172.31.0.3', 53, b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'))
log('U4 10.0.0.1:53 -> %s' % udp_send('10.0.0.1', 53, b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'))
log('U5 10.0.0.1:123 -> %s' % udp_send('10.0.0.1', 123, b'\x1b' + b'\x00' * 47))
log('U6 169.254.169.254:80 -> %s' % udp_send('169.254.169.254', 80, b'GET / HTTP/1.0\r\n\r\n'))
# P2 UDP 公网对照
log('U7 8.8.8.8:53 DNS -> %s' % udp_send('8.8.8.8', 53, b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'))
log('U8 8.8.8.8:123 -> %s' % udp_send('8.8.8.8', 123, b'\x1b' + b'\x00' * 47))
# P3 IPv6
log('V1 tcp6 2001:4860:8888::8:443 -> %s' % tcp6('2001:4860:8888::8', 443))
log('V2 tcp6 2606:4700:4700::1111:443 -> %s' % tcp6('2606:4700:4700::1111', 443))
log('V3 tcp6 fd00::1:80 -> %s' % tcp6('fd00::1', 80))
log('V4 tcp6 fe80::1:80 -> %s' % tcp6('fe80::1', 80))
log('V5 udp6 2001:4860:8888::8:53 -> %s' % udp6_send('2001:4860:8888::8', 53, b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'))
log('UDP6_DONE')
f.close()
