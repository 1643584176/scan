# -*- coding: utf-8 -*-
"""查 Data API 配置 + databases/roles 详情(PG 连接信息)"""
import http.client, ssl, json, sys
ctx = ssl.create_default_context()
ORG = 'org-flat-dawn-91601224'
key = json.load(open(r'D:\scan\neon_report\_apikey.json'))['key']
from _neon_creds_stage import API_HOST, API_BASE, HEADERS_TEST

ctx2 = {'pid': 'orange-sun-90493739', 'bid': 'br-wandering-field-w2ob6mpn'}

def req(method, path, body=None):
    conn = http.client.HTTPSConnection(API_HOST, context=ctx, timeout=40)
    h = {'User-Agent': 'netlify-cli/17.0.0', 'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + key}
    h.update(HEADERS_TEST)
    conn.request(method, API_BASE + path, body=json.dumps(body).encode() if body is not None else None, headers=h)
    r = conn.getresponse(); raw = r.read()
    st = r.status; conn.close()
    return st, raw

def show(tag, path, cut=1200):
    st, raw = req('GET', path)
    print('\n== %s -> %d' % (tag, st))
    try:
        print(json.dumps(json.loads(raw), indent=1, ensure_ascii=False)[:cut])
    except Exception:
        print(raw[:250])

P = ctx2['pid']; B = ctx2['bid']
show('data-api cfg', '/projects/%s/branches/%s/data-api/neondb' % (P, B), 1500)
show('databases', '/projects/%s/branches/%s/databases' % (P, B), 1200)
show('roles', '/projects/%s/branches/%s/roles' % (P, B), 1500)
show('branch detail', '/projects/%s/branches/%s' % (P, B), 1500)
