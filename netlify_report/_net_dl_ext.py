# -*- coding: utf-8 -*-
"""Netlify:自动分块下载 extension 二进制(probe9),重组到本地文件"""
import http.client, ssl, gzip, brotli, sys, json, time, base64
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_B

ctx = ssl.create_default_context()
CHUNK = 300000
TOTAL = 6234264  # probe5 测得

def fetch(start):
    conn = http.client.HTTPSConnection('sec-b-08v4pk.netlify.app', context=ctx, timeout=120)
    conn.request('GET', '/.netlify/functions/probe9?start=%d&size=%d' % (start, CHUNK))
    r = conn.getresponse()
    b = r.read()
    conn.close()
    if r.status != 200:
        raise RuntimeError('status %d: %s' % (r.status, b[:300].decode('utf-8', 'replace')))
    d = json.loads(b.decode('utf-8', 'replace'))
    return d

# 1. 先探测响应大小限制:拿第一块
d0 = fetch(0)
print('first chunk: total=%s len=%d (base64 %d bytes)' % (d0.get('total'), d0.get('len'), len(d0.get('b64', ''))))
total = d0.get('total') or TOTAL
print('total bytes:', total)

# 2. 全量下载
out = bytearray()
pos = 0
t0 = time.time()
while pos < total:
    d = fetch(pos)
    raw = base64.b64decode(d['b64'])
    out.extend(raw)
    pos += len(raw)
    print('  got %d / %d (%.0f%%)' % (pos, total, pos * 100.0 / total), flush=True)
    time.sleep(0.3)

path = r'D:\scan\netlify_report\_ext_binary.bin'
open(path, 'wb').write(bytes(out))
print('saved', path, len(out), 'bytes in %.0fs' % (time.time() - t0))
