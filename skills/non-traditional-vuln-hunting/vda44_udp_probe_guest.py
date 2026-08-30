# -*- coding: utf-8 -*-
"""vda44_udp_probe: UDP 出网三模式对照 (deny-all/allow-all/custom)
防火墙文档承诺拦截 outbound TCP + DNS; UDP 非 DNS 是否出网?
公网 NTP(123)/DNS(53) UDP 响应 = UDP 出网铁证 (防火墙不会代答 NTP)
输出: /vercel/sandbox/udp_probe_<mode>.out + 哨兵 UDPPROBE_DONE"""
import os, sys, time, socket, struct

MODE = sys.argv[1] if len(sys.argv) > 1 else 'unknown'
OUT = '/vercel/sandbox/udp_probe_%s.out' % MODE
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def dns_q(name='example.com', qtype=1):
    hdr = struct.pack('>HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
    q = b''.join(bytes([len(x)]) + x.encode() for x in name.split('.')) + b'\x00'
    return hdr + q + struct.pack('>HH', qtype, 1)


NTP = b'\x1b' + 47 * b'\x00'


def udp_probe(tag, ip, port, payload, t=4):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(t)
    t0 = time.time()
    try:
        s.sendto(payload, (ip, port))
        try:
            data, addr = s.recvfrom(2048)
            log('%s %s:%d -> RESP %dB %.1fs first=%s' % (tag, ip, port, len(data), time.time() - t0, data[:12].hex()))
        except socket.timeout:
            log('%s %s:%d -> SENT_NORESP %.1fs' % (tag, ip, port, time.time() - t0))
        except Exception as e:
            log('%s %s:%d -> RECV_ERR %s' % (tag, ip, port, e))
    except Exception as e:
        log('%s %s:%d -> SEND_ERR %s' % (tag, ip, port, e))
    finally:
        s.close()


def tcp_probe(tag, ip, port, t=4):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(t)
    t0 = time.time()
    try:
        s.connect((ip, port))
        log('%s %s:%d -> TCP_OPEN %.1fs' % (tag, ip, port, time.time() - t0))
    except Exception as e:
        log('%s %s:%d -> TCP_ERR %s' % (tag, ip, port, e))
    finally:
        s.close()


def main():
    log('=== UDP probe mode=%s ===' % MODE)
    # P1 公网 UDP (NTP/DNS 高响应率)
    udp_probe('dns', '8.8.8.8', 53, dns_q())
    udp_probe('dns', '1.1.1.1', 53, dns_q())
    udp_probe('ntp', '8.8.8.8', 123, NTP)
    udp_probe('ntp', '1.1.1.1', 123, NTP)
    udp_probe('rnd', '8.8.8.8', 9999, b'udp-probe-44')
    udp_probe('quic', '1.1.1.1', 443, b'\x00' * 120)
    # P2 私网 UDP
    udp_probe('dns-priv', '172.31.0.2', 53, dns_q())
    udp_probe('rnd-priv', '172.31.0.2', 9999, b'udp-probe-44')
    # P3 TCP 对照 (模式基线)
    tcp_probe('tcp', '8.8.8.8', 53)
    tcp_probe('tcp', 'httpbin.org', 443)
    tcp_probe('tcp', '172.31.0.2', 53)
    log('UDPPROBE_DONE')
    f.close()


if __name__ == '__main__':
    main()
