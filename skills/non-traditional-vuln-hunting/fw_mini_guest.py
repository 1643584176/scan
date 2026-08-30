# -*- coding: utf-8 -*-
"""fw_mini: 最小化探测 (每步落盘, 避免监控误杀)
1) 172.31.0.3:5432 SSLRequest
2) 172.31.0.2:53 TCP connect
3) httpbin.org:443 (对照)
输出落盘 + 哨兵 FWMINI_DONE"""
import socket, time, struct

OUT = '/vercel/sandbox/fwmini.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def probe(ip, port, payload, t=2.5, rt=1.5):
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
                if len(d) > 80:
                    break
        except socket.timeout:
            pass
        s.close()
        return 'OPEN DATA=%r' % d[:40] if d else 'OPEN_NODATA'
    except (ConnectionResetError, BrokenPipeError):
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


log('START')
pg = struct.pack('!II', 8, 80877103)
log('T1 172.31.0.3:5432 -> %s' % probe('172.31.0.3', 5432, pg))
log('T2 172.31.0.2:53 -> %s' % probe('172.31.0.2', 53, b'\x00'))
log('T3 172.31.0.2:443 -> %s' % probe('172.31.0.2', 443, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n'))
log('T4 httpbin.org:443 -> %s' % probe('httpbin.org', 443, b'GET / HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n'))
log('FWMINI_DONE')
f.close()
