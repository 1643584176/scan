# -*- coding: utf-8 -*-
"""http_probe: 私有网段真实服务 vs 防火墙模拟 区分
在 custom 放行网段内对常见服务端口发送 HTTP GET，观察:
- 真实服务 -> HTTP 响应头
- 防火墙模拟/黑洞 -> NODATA 或 RST
目标: 10.0.0.1/2, 10.1.0.1, 10.100.0.1, 172.31.0.1/2/3, 100.64.0.1, 192.168.0.1, 169.254.169.254
端口: 80/443/8080/3000/5000 (HTTP GET), 22 (SSH banner), 3306 (MySQL), 6379 (Redis), 27017 (Mongo)
输出落盘 + 哨兵 HTTPP_DONE"""
import socket, time

OUT = '/vercel/sandbox/httpp.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def probe(ip, port, payload, t=2.0, rt=1.2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect((ip, port))
        if payload:
            s.sendall(payload)
        s.settimeout(rt)
        d = b''
        try:
            while True:
                ch = s.recv(4096)
                if not ch:
                    break
                d += ch
                if len(d) > 200:
                    break
        except socket.timeout:
            pass
        s.close()
        return 'DATA=%r' % d[:80] if d else 'NODATA'
    except (ConnectionResetError, BrokenPipeError):
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


GET80 = b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n'
SSH = b'\x00\x00\x00\x0c\x04\x00\x00\x00\x00\x00\x00\x00'
log('START')
targets = [
    ('10.0.0.1', [80, 443, 8080]), ('10.0.0.2', [80, 443, 8080]), ('10.1.0.1', [80, 8080]),
    ('10.100.0.1', [80, 8080]), ('10.200.0.1', [80, 8080]), ('172.31.0.1', [80, 443, 8080]),
    ('172.31.0.2', [80, 8080, 3306]), ('172.31.0.3', [80, 8080]), ('100.64.0.1', [80, 443]),
    ('100.64.0.2', [80, 8080]), ('192.168.0.1', [80, 8080]), ('192.168.1.1', [80, 443]),
    ('169.254.169.254', [80, 443]), ('169.254.169.253', [80, 8080]),
]
for ip, ports in targets:
    for p in ports:
        log('H %s:%d -> %s' % (ip, p, probe(ip, p, GET80)))
log('--- banners ---')
for ip in ['10.0.0.1', '10.0.0.2', '172.31.0.1', '172.31.0.2', '172.31.0.3', '192.168.0.1']:
    log('B %s:22 -> %s' % (ip, probe(ip, 22, SSH)))
    log('B %s:3306 -> %s' % (ip, probe(ip, 3306, b'\x0a\x00\x00\x00\x0a')))
    log('B %s:6379 -> %s' % (ip, probe(ip, 6379, b'PING\r\n')))
log('HTTPP_DONE')
f.close()
