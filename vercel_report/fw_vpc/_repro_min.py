# -*- coding: utf-8 -*-
"""Vercel Sandbox custom-policy private-range bypass - minimal repro
Run INSIDE a Vercel Sandbox with network policy:
  {"mode": "custom", "allowedDomains": ["httpbin.org"]}
Only TCP connect + 8-byte PG SSLRequest (no auth, no data read).
Expected: custom -> b'S' (reachable) | allow-all / deny-all -> errno 113
"""
import socket, struct, sys

TARGETS = [('172.31.0.3', 5432), ('172.31.0.2', 5432), ('10.0.0.2', 5432), ('192.168.0.2', 5432)]

def probe(ip, port, timeout=2.5):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
    except OSError as e:
        return 'OSERR:%d' % (e.errno or -1)
    try:
        s.sendall(struct.pack('!II', 8, 80877103))   # PG SSLRequest
        data = s.recv(8)
        return 'OPEN DATA=%r' % data
    except Exception as e:
        return 'OPEN ERR:%s' % e
    finally:
        s.close()

if __name__ == '__main__':
    for ip, port in TARGETS:
        print('%s:%d -> %s' % (ip, port, probe(ip, port)), flush=True)
    sys.exit(0)
