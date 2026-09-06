# -*- coding: utf-8 -*-
"""Connectivity check for the three candidate targets."""
import socket
import time

hosts = [
    ('api.faraday.ai', 443), ('app.faraday.ai', 443), ('vault2.faraday.ai', 443),
    ('row.pro', 443),
    ('api.mergify.com', 443), ('dashboard.mergify.com', 443),
    ('matomo.cloud', 443), ('demo.matomo.cloud', 443),
    ('api.matomo.org', 443), ('raw.githubusercontent.com', 443),
    ('github.com', 443), ('hackerone.com', 443),
]

def chk(host, port, timeout=6):
    t0 = time.time()
    try:
        socket.create_connection((host, port), timeout=timeout)
        return 'OPEN   %.0fms' % ((time.time() - t0) * 1000)
    except Exception as e:
        return 'FAIL   %s' % type(e).__name__

for h, p in hosts:
    print('%-28s %-6s %s' % (h, p, chk(h, p)))
