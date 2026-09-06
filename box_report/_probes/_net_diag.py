# -*- coding: utf-8 -*-
"""Probe local/known proxies and Google reachability through them."""
import socket
import threading
import requests
import urllib3

urllib3.disable_warnings()

CANDIDATES = [
    ('192.168.0.199', 1080, 'old-lan-proxy'),
    ('127.0.0.1', 7890, 'clash'),
    ('127.0.0.1', 7897, 'clash-verge'),
    ('127.0.0.1', 1080, 'local-socks'),
    ('127.0.0.1', 10808, 'v2ray'),
    ('127.0.0.1', 10809, 'v2ray-http'),
    ('127.0.0.1', 8889, 'proxy'),
    ('127.0.0.1', 33210, 'clash-misc'),
]

def port_open(host, port, timeout=1.5):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False

print('== TCP port check ==')
open_ones = []
for h, p, tag in CANDIDATES:
    ok = port_open(h, p)
    print('%-18s:%-6d %-14s %s' % (h, p, tag, 'OPEN' if ok else 'closed'))
    if ok:
        open_ones.append((h, p, tag))

print()
print('== HTTP proxy check (google) ==')
for h, p, tag in open_ones:
    proxies = {'http': 'http://%s:%d' % (h, p), 'https': 'http://%s:%d' % (h, p)}
    try:
        r = requests.get('https://www.google.com/generate_204', proxies=proxies,
                         timeout=6, verify=False)
        print('%-18s:%-6d google 204 -> %d' % (h, p, r.status_code))
    except Exception as e:
        print('%-18s:%-6d google FAIL: %s' % (h, p, str(e)[:80]))
    try:
        r = requests.get('https://api.ipify.org', proxies=proxies, timeout=6, verify=False)
        print('%-18s:%-6d exit IP  -> %s' % (h, p, r.text.strip()[:40]))
    except Exception as e:
        print('%-18s:%-6d ipify FAIL: %s' % (h, p, str(e)[:80]))
    print()
