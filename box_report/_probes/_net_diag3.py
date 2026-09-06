# -*- coding: utf-8 -*-
"""Parallel reachability check for Box-related hosts (1 req each, short timeout)."""
import socket
import concurrent.futures

HOSTS = [
    'app.box.com', 'api.box.com', 'account.box.com', 'dl.boxcloud.com',
    'upload.box.com', 'notes.services.box.com', 'cloud.app.box.com',
    'm.box.com', 'developer.box.com', 'www.box.com',
    'raw.githubusercontent.com', 'github.com', 'static.boxcdn.net',
    'cdn.box.com', 'assets.boxcloud.com', 'public.boxcloud.com',
]

def check(h):
    try:
        ip = socket.gethostbyname(h)
    except Exception as e:
        return (h, 'DNS-FAIL', str(e)[:40])
    try:
        s = socket.create_connection((h, 443), timeout=5)
        s.close()
        return (h, 'TCP-OK', ip)
    except Exception as e:
        return (h, 'TCP-FAIL', ip)

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    for h, st, ip in ex.map(check, HOSTS):
        print('%-28s %-10s %s' % (h, st, ip))
