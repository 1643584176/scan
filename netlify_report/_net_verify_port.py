# -*- coding: utf-8 -*-
"""verify 端口语义:domain:port 是否生效 + httpforever 本地对照"""
import http.client, ssl, gzip, brotli, json, sys, time, urllib.parse, socket
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A

ctx = ssl.create_default_context()

def req(path, timeout=30):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Cookie': COOKIE_A}
    t0 = time.time()
    conn.request('GET', path, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br': raw = brotli.decompress(raw)
    elif enc == 'gzip': raw = gzip.decompress(raw)
    dt = time.time() - t0
    conn.close()
    return r.status, raw.decode('utf-8', 'ignore').replace('\n', ' ')[:200], dt

def show(label, dom):
    p = '/.netlify/functions/verify?domain=' + urllib.parse.quote(dom, safe='')
    st, raw, dt = req(p)
    print('%-30s %s %6.1fs | %s' % (label, st, dt, raw))

print('--- 本地对照:httpforever.com 端口状态 ---')
for port in (80, 443):
    try:
        t0 = time.time()
        with socket.create_connection(('httpforever.com', port), timeout=4):
            print('httpforever.com:%d OPEN %.1fs' % (port, time.time() - t0))
    except Exception as e:
        print('httpforever.com:%d %s %.1fs' % (port, type(e).__name__, time.time() - t0))

print()
print('--- verify domain:port 语义 ---')
show('example.com:80',       'example.com:80')
show('example.com:8080',     'example.com:8080')
show('example.com:8443',     'example.com:8443')
show('nip10:80',             '10.255.255.1.nip.io:80')
show('nip10:443',            '10.255.255.1.nip.io:443')
show('nip127:80',            '127.0.0.1.nip.io:80')
show('nip127:443',           '127.0.0.1.nip.io:443')
show('nip127:9001',          '127.0.0.1.nip.io:9001')
print()
print('--- 内网/链路地址探测 ---')
show('link dns :53',         '169.254.100.5.nip.io:53')
show('link gw :9001',        '169.254.100.1.nip.io:9001')
show('link self :9001',      '169.254.100.6.nip.io:9001')
show('k8s api :443',         '10.96.0.1.nip.io:443')
show('k8s api :80',          '10.96.0.1.nip.io:80')
show('pub 8.8.8.8:53',       '8.8.8.8.nip.io:53')
print('done')
