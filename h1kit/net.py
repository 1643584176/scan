# -*- coding: utf-8 -*-
"""
net.py - network helpers used before/while testing a target.

  - check_hosts():  parallel TCP reachability for a list of hosts
  - probe_proxies(): discover working local/LAN proxies + google reachability
  - http_get():      single low-volume HTTPS GET (manual-probe friendly)
  - exit_ip():       current egress IP (direct or via proxy)

Usage:
    from h1kit import net
    net.check_hosts(['app.box.com', 'api.github.com'])
    net.probe_proxies()
"""
import concurrent.futures
import http.client
import socket
import ssl
import urllib.request

DEFAULT_PROXY_CANDIDATES = [
    ('192.168.0.199', 1080, 'old-lan-proxy'),
    ('127.0.0.1', 7890, 'clash'),
    ('127.0.0.1', 7897, 'clash-verge'),
    ('127.0.0.1', 1080, 'local-socks'),
    ('127.0.0.1', 10808, 'v2ray'),
    ('127.0.0.1', 10809, 'v2ray-http'),
    ('127.0.0.1', 8889, 'proxy'),
    ('127.0.0.1', 33210, 'clash-misc'),
]


def check_hosts(hosts, port=443, timeout=5):
    """Parallel TCP connect check; returns [(host, 'TCP-OK'|'TCP-FAIL'|'DNS-FAIL', ip)]."""
    def one(h):
        try:
            ip = socket.gethostbyname(h)
        except Exception:
            return (h, 'DNS-FAIL', '-')
        try:
            s = socket.create_connection((h, port), timeout=timeout)
            s.close()
            return (h, 'TCP-OK', ip)
        except Exception:
            return (h, 'TCP-FAIL', ip)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(one, hosts))
    for h, st, ip in res:
        print('%-30s %-10s %s' % (h, st, ip))
    return res


def probe_proxies(candidates=None, google_url='https://www.google.com/generate_204',
                  ipify_url='https://api.ipify.org', timeout=6):
    """
    TCP-check candidate proxies, then verify google + egress IP through each
    open one. Prints a report; returns list of working (host, port, tag).
    """
    candidates = candidates or DEFAULT_PROXY_CANDIDATES
    print('== TCP port check ==')
    open_ones = []
    for h, p, tag in candidates:
        try:
            s = socket.create_connection((h, p), timeout=1.5)
            s.close()
            print('%-18s:%-6d %-14s OPEN' % (h, p, tag))
            open_ones.append((h, p, tag))
        except Exception:
            print('%-18s:%-6d %-14s closed' % (h, p, tag))
    print()
    working = []
    for h, p, tag in open_ones:
        proxy = 'http://%s:%d' % (h, p)
        proxies = {'http': proxy, 'https': proxy}
        for name, url in (('google', google_url), ('exit-ip', ipify_url)):
            try:
                body = _open(url, timeout, proxies)
                print('%-18s:%-6d %-8s OK %s' % (h, p, name, body[:40]))
            except Exception as e:
                print('%-18s:%-6d %-8s FAIL %s' % (h, p, name, str(e)[:60]))
        working.append((h, p, tag))
    return working


def _open(url, timeout, proxies=None, max_bytes=2048):
    """urlopen that honours an explicit http proxy dict (urllib has no
    per-call proxies kwarg - must build an opener with ProxyHandler)."""
    req = urllib.request.Request(url, headers={'User-Agent': 'h1kit/1.0'})
    if proxies:
        handler = urllib.request.ProxyHandler(
            {'http': proxies['http'], 'https': proxies['https']})
    else:
        handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(handler)
    with opener.open(req, timeout=timeout) as r:
        return r.read(max_bytes).decode('utf-8', 'replace').strip()


def exit_ip(proxies=None, timeout=8):
    """Egress IP, optionally via an http proxy dict {'http':..., 'https':...}."""
    try:
        return _open('https://api.ipify.org', timeout, proxies)
    except Exception as e:
        return 'FAIL: %s' % str(e)[:80]


def http_get(host, path='/', port=443, headers=None, timeout=20, max_bytes=3000000):
    """
    Single low-volume HTTPS GET (no redirect following).
    Returns (status, resp_headers, body_bytes).
    """
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(host, port, timeout=timeout, context=ctx)
    hdrs = {'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/126.0.0.0 Safari/537.36'),
            'Accept': 'text/html,application/json'}
    if headers:
        hdrs.update(headers)
    conn.request('GET', path, headers=hdrs)
    r = conn.getresponse()
    raw = r.read(max_bytes)
    h = {k.lower(): v for k, v in r.getheaders()}
    conn.close()
    return r.status, h, raw
