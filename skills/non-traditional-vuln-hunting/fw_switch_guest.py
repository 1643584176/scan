# -*- coding: utf-8 -*-
"""fw_switch: 同沙箱策略切换对照 (allow-all -> custom)
1) 当前策略下测 172.31 采样 (PG IP + DNS)
2) 切换到 custom -> 再测
输出落盘 + 哨兵 FWSW_DONE"""
import socket, time, struct

OUT = '/vercel/sandbox/fwsw.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def probe(ip, port, payload, t=2.0, rt=1.5):
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
                if len(d) > 100:
                    break
        except socket.timeout:
            pass
        s.close()
        return 'OPEN DATA=%r' % d[:60] if d else 'OPEN_NODATA'
    except (ConnectionResetError, BrokenPipeError):
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception:
        return 'EXC'


def run_phase(tag):
    log('=== %s ===' % tag)
    pg = struct.pack('!II', 8, 80877103)
    targets = [('172.31.0.3', 5432, pg), ('172.31.0.4', 5432, pg), ('172.31.0.81', 5432, pg),
               ('172.31.0.101', 5432, pg), ('172.31.0.140', 5432, pg), ('172.31.0.200', 5432, pg),
               ('172.31.57.1', 5432, pg), ('172.31.250.254', 5432, pg),
               ('172.31.0.2', 53, b'\x00'), ('172.31.0.2', 443, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n'),
               ('172.31.0.2', 23456, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n'),
               ('httpbin.org', 443, b'GET / HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n')]
    for ip, p, payload in targets:
        log('%s:%d -> %s' % (ip, p, probe(ip, p, payload)))
        time.sleep(0.2)


run_phase('PHASE1 当前策略')
log('FWSW_DONE')
f.close()
