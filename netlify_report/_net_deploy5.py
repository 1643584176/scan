# -*- coding: utf-8 -*-
"""Netlify:发布 deploy(PUT 更新)"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import AUTH_HEADER

SITE_ID = '04f08ff6-f274-47ac-b6d7-5fb1e055f3b4'
DEPLOY_ID = '6a97a380a47ffb3bbe868775'
ctx = ssl.create_default_context()

def api(path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': AUTH_HEADER, 'Content-Type': 'application/json'}
    payload = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=payload, headers=h)
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

for body in [{'state': 'published'}, {'draft': False}, {'state': 'ready'}]:
    s, raw = api('/api/v1/sites/%s/deploys/%s' % (SITE_ID, DEPLOY_ID), method='PUT', body=body)
    print('PUT %s: %d %s' % (body, s, raw[:150].decode('utf-8', 'ignore').replace('\n', ' ')))
    if s == 200:
        d = json.loads(raw)
        print('  state:', d.get('state'), 'published_at:', d.get('published_at'))
        if d.get('state') == 'published':
            break
