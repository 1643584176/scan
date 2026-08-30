# -*- coding: utf-8 -*-
"""D 线: custom 模式 VPC payload 探测 (并行快速版 v3)
172.31.0.0/24 关键端口带 payload 连接, 分类: DATA(真实服务) / RST / NODATA / TIMEOUT
两阶段: 非阻塞连接 -> select 可写 -> send payload -> 阻塞读 (短超时)
"""
import socket, time, struct, select, random

OUT = '/vercel/sandbox/fwcustom4b.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def main():
    HTTP = b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n'
    PORTS = {23456: HTTP, 26661: HTTP, 33090: HTTP, 34121: HTTP,
             30001: HTTP, 30002: HTTP, 8080: HTTP, 9090: HTTP,
             80: HTTP, 443: HTTP, 22: b'SSH-2.0-probe\r\n',
             5432: struct.pack('!II', 8, 0x04D2162F), 6379: b'PING\r\n'}

    tasks = [('172.31.0.%d' % i, p, payload) for i in range(1, 255) for p, payload in PORTS.items()]
    random.shuffle(tasks)
    log('total tasks: %d' % len(tasks))

    hits = []
    deadline_total = time.time() + 135

    for batch_start in range(0, len(tasks), 100):
        if time.time() > deadline_total:
            log('deadline, break at %d' % batch_start)
            break
        batch = tasks[batch_start:batch_start + 100]
        conns = {}  # sock -> (ip, port, payload)
        for ip, p, payload in batch:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setblocking(False)
                err = s.connect_ex((ip, p))
                if err in (0, 10035, 115):
                    conns[s] = (ip, p, payload)
                else:
                    s.close()
            except Exception:
                pass

        # 阶段1: 等待可写 (连接完成)
        ready = []  # (sock, ip, port, payload)
        end = time.time() + 2.0
        while conns and time.time() < end:
            try:
                _, w, _ = select.select([], list(conns.keys()), [], 0.2)
            except Exception:
                break
            for s in w:
                ip, p, payload = conns.pop(s)
                try:
                    err = s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                    if err == 0:
                        ready.append((s, ip, p, payload))
                    else:
                        s.close()
                except Exception:
                    s.close()
        for s in list(conns.keys()):
            try:
                s.close()
            except Exception:
                pass

        # 阶段2: 发 payload + 读响应 (阻塞短超时)
        for s, ip, p, payload in ready:
            try:
                s.setblocking(True)
                s.settimeout(1.8)
                s.sendall(payload)
                d = b''
                try:
                    while True:
                        ch = s.recv(4096)
                        if not ch:
                            break
                        d += ch
                        if len(d) > 500:
                            break
                except socket.timeout:
                    pass
                s.close()
                if d:
                    r = 'DATA %r' % d[:150]
                    hits.append((ip, p, r))
                    log('HIT %s:%d %s' % (ip, p, r))
            except (ConnectionResetError, BrokenPipeError):
                try:
                    s.close()
                except Exception:
                    pass
            except Exception:
                try:
                    s.close()
                except Exception:
                    pass

        if batch_start % 1000 == 0:
            log('progress %d/%d, hits=%d' % (batch_start, len(tasks), len(hits)))

    log('total hits: %s' % hits)
    log('FWCUSTOM4B_DONE')
    f.close()


if __name__ == '__main__':
    main()
