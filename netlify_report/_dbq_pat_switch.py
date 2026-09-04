# -*- coding: utf-8 -*-
"""PAT 通道 + expose_owner_credentials_to_pat 开关行为验证(自己 site,测完还原)
1. PAT 调 database-query(current_user?)——开关默认 false
2. GET /database(PAT)——是否返回 owner 串
3. PUT settings=true -> 重测 1/2 -> PUT settings=false 还原
"""
import http.client, ssl, gzip, brotli, json, sys, time
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import TOKEN_A, SITE_A

ctx = ssl.create_default_context()


def dbq_pat(sql, role=None):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept-Encoding': 'br, gzip', 'Accept': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A, 'Content-Type': 'application/json'}
    body = {'siteId': SITE_A, 'branchId': 'production', 'action': 'query', 'sql': sql}
    if role:
        body['role'] = role
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'br':
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:800].decode('utf-8', 'ignore')
    conn.close()
    return st, out


def api(method, path, body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=30)
    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0',
         'Accept': 'application/json', 'Content-Type': 'application/json',
         'Authorization': 'Bearer ' + TOKEN_A}
    b = json.dumps(body).encode() if body is not None else None
    conn.request(method, path, body=b, headers=h)
    r = conn.getresponse()
    raw = r.read()
    enc = r.getheader('Content-Encoding')
    if enc == 'gzip':
        raw = gzip.decompress(raw)
    st = r.status
    out = raw[:800].decode('utf-8', 'ignore')
    conn.close()
    return st, out


SQL = 'select current_user::text as u'
print('== 默认(开关 false)PAT 行为 ==')
st, out = dbq_pat(SQL)
print('PAT dbq(owner):        [%d] %s' % (st, out[:200]))
st, out = dbq_pat(SQL, role='readonly')
print('PAT dbq(readonly):     [%d] %s' % (st, out[:200]))
st, out = api('GET', '/api/v1/sites/%s/database' % SITE_A)
print('PAT GET /database:     [%d] %s' % (st, out[:300]))
print()

print('== 翻转开关 -> true ==')
st, out = api('PUT', '/api/v1/sites/%s/database/settings' % SITE_A, {'expose_owner_credentials_to_pat': True})
print('PUT settings(true):    [%d] %s' % (st, out[:200]))
st, out = api('GET', '/api/v1/sites/%s/database/settings' % SITE_A)
print('GET settings:          [%d] %s' % (st, out[:200]))
st, out = dbq_pat(SQL)
print('PAT dbq(owner):        [%d] %s' % (st, out[:200]))
st, out = api('GET', '/api/v1/sites/%s/database' % SITE_A)
print('PAT GET /database:     [%d] %s' % (st, out[:300]))
print()

print('== 还原 -> false ==')
st, out = api('PUT', '/api/v1/sites/%s/database/settings' % SITE_A, {'expose_owner_credentials_to_pat': False})
print('PUT settings(false):   [%d] %s' % (st, out[:200]))
st, out = api('GET', '/api/v1/sites/%s/database/settings' % SITE_A)
print('GET settings:          [%d] %s' % (st, out[:200]))
