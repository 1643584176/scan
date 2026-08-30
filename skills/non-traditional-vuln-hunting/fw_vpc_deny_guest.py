# -*- coding: utf-8 -*-
"""fw_vpc_deny: deny-all 模式下 172.31 VPC 可达性对比
1) 已知 PG IP x 5432 (12 个)
2) 172.31.0.0/24 5432 快速扫描 (并行非阻塞)
3) 172.31.0.2 各端口采样
4) 公网对照 (httpbin.org 应全拦)
输出落盘 + 哨兵 FWDENY_DONE"""
import socket, time, struct, random, select

OUT = '/vercel/sandbox/fwdeny.out'
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
        return 'DATA %r' % d[:80] if d else 'OPEN_NODATA'
    except (ConnectionResetError, BrokenPipeError):
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception:
        return 'EXC'


def main():
    # 1) 已知 PG IP 采样
    log('=== P1 已知 PG IP x 5432 (deny-all) ===')
    hits = ['172.31.0.3', '172.31.0.4', '172.31.0.18', '172.31.0.81', '172.31.0.94',
            '172.31.0.101', '172.31.0.125', '172.31.0.140', '172.31.0.200', '172.31.0.241']
    for ip in hits:
        log('%s:5432 -> %s' % (ip, probe(ip, 5432, struct.pack('!II', 8, 80877103))))
        time.sleep(0.15)

    # 2) 172.31.0.0/24 5432 并行快速扫描
    log('=== P2 172.31.0.0/24 x 5432 并行 ===')
    payload = struct.pack('!II', 8, 80877103)
    socks = {}
    for i in range(1, 255):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setblocking(False)
            err = s.connect_ex(('172.31.0.%d' % i, 5432))
            if err in (0, 10035, 115):
                socks[s] = i
            else:
                s.close()
        except Exception:
            pass
    opened = []
    end = time.time() + 3
    while socks and time.time() < end:
        try:
            _, w, _ = select.select([], list(socks.keys()), [], 0.3)
        except Exception:
            break
        for s in w:
            ip = socks.pop(s)
            try:
                err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if err == 0:
                    opened.append(ip)
            except Exception:
                pass
            try:
                s.close()
            except Exception:
                pass
    for s in list(socks.keys()):
        try:
            s.close()
        except Exception:
            pass
    log('open ips: %d -> %s' % (len(opened), opened))

    # 3) 172.31.0.2 端口采样
    log('=== P3 172.31.0.2 端口采样 ===')
    for p in [22, 53, 80, 443, 23456, 26661, 33090, 34121, 5432, 8080, 9090]:
        log('172.31.0.2:%d -> %s' % (p, probe('172.31.0.2', p, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n' if p != 5432 else struct.pack('!II', 8, 80877103))))
        time.sleep(0.15)

    # 4) 公网对照
    log('=== P4 公网对照 ===')
    log('httpbin.org:443 -> %s' % probe('34.202.68.214', 443, b'GET / HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n'))
    log('8.8.8.8:53 -> %s' % probe('8.8.8.8', 53, b'\x00'))
    log('100.64.0.1:23456 -> %s' % probe('100.64.0.1', 23456, b'GET / HTTP/1.1\r\nHost: x\r\n\r\n'))

    log('FWDENY_DONE')
    f.close()


if __name__ == '__main__':
    main()
