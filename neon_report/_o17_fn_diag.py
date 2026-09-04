# -*- coding: utf-8 -*-
"""compute 域 403 深度诊断:响应头/cookie/Host 变体"""
import http.client, ssl, socket

ctx = ssl.create_default_context()
HOST = 'br-wandering-field-w2ob6mpn-secfn22529870.compute.c-1.us-east-2.aws.neon.build'

def call(method='GET', path='/', headers=None, host=None):
    try:
        conn = http.client.HTTPSConnection(host or HOST, context=ctx, timeout=20)
        h = {'User-Agent': 'Mozilla/5.0'}
        if headers:
            h.update(headers)
        conn.request(method, path, headers=h)
        r = conn.getresponse()
        data = r.read().decode('utf-8', 'replace')
        out = {'status': r.status, 'hdrs': dict(r.getheaders()), 'body': data[:200]}
        conn.close()
        return out
    except Exception as e:
        return {'status': -1, 'hdrs': {}, 'body': 'EXC %s' % e}

import sys, os, re, json as _j
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _neon_creds_stage import cookie_str

def json_dump(d):
    return _j.dumps({k: str(v)[:80] for k, v in d.items()}, default=str)

r = call(headers={'Cookie': cookie_str(), 'X-Bug-Bounty': 'xxbo'})
print('[console-cookie] %d' % r['status'], flush=True)
print(' hdrs:', json_dump(r['hdrs']), flush=True)
print(' body:', r['body'].replace('\n', ' ')[:150], flush=True)

# 响应头(默认请求)
r = call()
print('\n[default] %d' % r['status'], flush=True)
print(' hdrs:', json_dump(r['hdrs']), flush=True)

# DNS 解析 + IP 直连(SNI 保留)
try:
    ip = socket.gethostbyname(HOST)
    print('\nip:', ip, flush=True)
    r = call(headers={'Host': HOST})
    print('[ip-direct] %d' % r['status'], flush=True)
except Exception as e:
    print('dns err:', e, flush=True)

# Host 变体
for h2 in ['compute.neon.build', 'x.compute.c-1.us-east-2.aws.neon.build',
           HOST.replace('br-wandering-field-w2ob6mpn-', ''), 'localhost']:
    try:
        conn = http.client.HTTPSConnection(HOST, context=ctx, timeout=15)
        conn.request('GET', '/', headers={'Host': h2, 'User-Agent': 'Mozilla/5.0'})
        r2 = conn.getresponse()
        b2 = r2.read().decode('utf-8', 'replace')
        conn.close()
        print('[host=%s] %d %s' % (h2[:50], r2.status, b2[:120].replace('\n', ' ')), flush=True)
    except Exception as e:
        print('[host=%s] EXC %s' % (h2[:50], e), flush=True)
