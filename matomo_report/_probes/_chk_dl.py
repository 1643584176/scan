# -*- coding: utf-8 -*-
"""Check reachability of php/mariadb download sources."""
import socket
import time

hosts = [
    ('windows.php.net', 443),
    ('downloads.mariadb.org', 443),
    ('archive.mariadb.org', 443),
    ('dev.mysql.com', 443),
    ('cdn.jsdelivr.net', 443),
]

def chk(host, port, timeout=8):
    t0 = time.time()
    try:
        socket.create_connection((host, port), timeout=timeout)
        return 'OPEN  %dms' % ((time.time() - t0) * 1000)
    except Exception as e:
        return 'FAIL  %s' % type(e).__name__

for h, p in hosts:
    print('%-28s %-5d %s' % (h, p, chk(h, p)))
