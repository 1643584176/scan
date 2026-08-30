# -*- coding: utf-8 -*-
"""探测脚本: IP 模式 + 33090/34121 Freebox 指纹 (通用)"""
import os, time, socket

OUT = '/vercel/sandbox/fb90.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def main():
    # 本机 IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('100.64.0.1', 53))
        ip = s.getsockname()[0]
        s.close()
        log('self ip: %s' % ip)
    except Exception as e:
        log('ip ERR %s' % e)
        ip = '127.0.0.1'

    for port in [33090, 34121]:
        for target in [ip, '127.0.0.1']:
            try:
                c = socket.create_connection((target, port), timeout=3)
                log('conn %s:%d OPEN' % (target, port))
                c.sendall(b'GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n')
                c.settimeout(4)
                data = b''
                try:
                    while True:
                        chunk = c.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                        if len(data) > 2000:
                            break
                except socket.timeout:
                    pass
                c.close()
                log('resp: %s' % data[:1200])
            except Exception as e:
                log('conn %s:%d -> %s' % (target, port, type(e).__name__))

    log('FB90_DONE')
    f.close()


if __name__ == '__main__':
    main()
