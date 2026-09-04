# -*- coding: utf-8 -*-
"""Netlify:database-query 401 语义确认
问题:A->B 返回 401,是权限校验还是连接查询差异?
变体:
  1. A + 随机不存在 siteId
  2. A + A 的另一个无库站点
  3. A + B site(有库,无权限)= 401 基线
  4. B 删库后:A + B site -> 看是否变化
  5. 401 vs 404 语义:对比不同 siteId 类型
"""
import http.client, ssl, gzip, brotli, sys, json, uuid
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, COOKIE_B, SITE_A, TOKEN_A

ctx = ssl.create_default_context()
SITE_B = 'd2977de0-d24d-4544-81cb-933e610cad7d'

def call_fn(cookie, site_id, action='check', sql=None, host='app.netlify.com'):
    conn = http.client.HTTPSConnection(host, context=ctx, timeout=40)
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

def api_a(path, method='GET', body=None):
    conn = http.client.HTTPSConnection('api.netlify.com', context=ctx, timeout=40)
    h = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'br, gzip',
         'Authorization': 'Bearer ' + TOKEN_A, 'Content-Type': 'application/json'}
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

# 1. 随机不存在 siteId / 自有无库站点 / 跨账号
# 先建 A 无库站点
s, raw = api_a('/api/v1/sites', method='POST', body={'name': 'sec-a-nodb'})
d = json.loads(raw)
sid_nodb = d.get('id')
print('A second site(no db):', s, sid_nodb)
rid = str(uuid.uuid4())
for label, cookie, sid in [
    ('A+rand id     ', COOKIE_A, rid),
    ('A+own no-db   ', COOKIE_A, sid_nodb),
    ('A->B cross    ', COOKIE_A, SITE_B),
]:
    st, raw = call_fn(cookie, sid)
    print('%s %d %s' % (label, st, raw[:100].decode('utf-8', 'ignore').replace('\n', ' ')))

# 2. B 删除数据库,再看 A->B
s, raw = api_a('/api/v1/sites/%s/database' % SITE_B, method='DELETE', body={})
print('B delete db (A token, should fail if no perm):', s, raw[:80].decode('utf-8', 'ignore'))

# 用 B token 删(需要 B 的 API token—— cookie 不能调 api.netlify.com?
# 用 cookie 换 access token 的方式:B cookie + app.netlify.com 内部?简化:直接 B cookie 试 app 域删除
conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=40)
h = {'User-Agent': 'Mozilla/5.0', 'Cookie': COOKIE_B, 'Content-Type': 'application/json'}
conn.request('POST', '/.netlify/functions/database-query',
             body=json.dumps({'siteId': SITE_B, 'action': 'check'}).encode(), headers=h)
r = conn.getresponse()
print('B->B before delete db:', r.status)
conn.close()
