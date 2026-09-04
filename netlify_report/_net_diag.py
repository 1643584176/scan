# -*- coding: utf-8 -*-
"""Netlify:诊断 - 分步打印状态(无缓冲),看卡在哪一步"""
import http.client, ssl, gzip, brotli, sys, json, time, hashlib
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()

def api(path, method='GET', body=None, raw_body=None, ctype='application/json', qs='', timeout=25):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'netlify-cli/17.0.0 (node v24)', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A, 'Content-Type': ctype}
    payload = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path + qs, body=payload, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    conn.close()
    return st, raw

# 0. 快速连通性
print('[0] api.netlify.com ping...', flush=True)
t0 = time.time()
try:
    s, raw = api('/api/v1/sites/%s' % SITE_A, timeout=15)
    print('    site GET:', s, '%.1fs' % (time.time() - t0), flush=True)
except Exception as e:
    print('    ERR:', str(e)[:120], flush=True)
